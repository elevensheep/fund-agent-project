import asyncio
import json
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import websockets

from core.config import get_settings
from core.database import async_session_factory, init_db
from core.models import StockMinutePrice
from shared_core.logger import logger
from workers.kis_client import KISClient
from workers.watchlist_manager import WatchlistManager


class RealtimeStreamWorker:
    """
    한국투자증권(KIS) WebSocket 실시간 틱 수신 및
    1분봉 롤링 버퍼링 ➡️ PostgreSQL 비동기 벌크 적재 백그라운드 데몬 (No LLM).
    """

    def __init__(
        self,
        tickers: Optional[List[str]] = None,
        flush_interval: float = 1.0,
    ):
        self.settings = get_settings()
        self.watchlist_mgr = WatchlistManager(tickers)
        self.kis_client = KISClient()
        self.buffer: List[Dict[str, Any]] = []
        self.flush_interval = flush_interval
        self._running = False

    def parse_kis_tick(self, raw_msg: str) -> Optional[Dict[str, Any]]:
        """
        KIS 실시간 체결가 메시지 파싱
        포맷: 0|H0STCNT0|001|005930^090102^75000^2^...
        또는 005930^090102^75000...
        """
        try:
            # 헤더 구분자 '|' 분리
            content = raw_msg
            if "|" in raw_msg:
                parts = raw_msg.split("|")
                if len(parts) >= 4:
                    content = parts[3]

            if "^" in content:
                fields = content.split("^")
                if len(fields) >= 13:
                    ticker = fields[0]
                    price = float(fields[2])
                    change_rate = float(fields[5]) if fields[5] else 0.0
                    volume = int(fields[12]) if fields[12].isdigit() else 100
                    return {
                        "ticker": ticker,
                        "open_price": float(fields[7]) if len(fields) > 7 and fields[7].isdigit() else price,
                        "high_price": float(fields[8]) if len(fields) > 8 and fields[8].isdigit() else price,
                        "low_price": float(fields[9]) if len(fields) > 9 and fields[9].isdigit() else price,
                        "close_price": price,
                        "volume": volume,
                        "change_rate": change_rate,
                    }
            elif raw_msg.startswith("{"):
                data = json.loads(raw_msg)
                if "body" in data and "output" in data["body"]:
                    out = data["body"]["output"]
                    return {
                        "ticker": out.get("stck_shrn_iscd", "005930"),
                        "open_price": float(out.get("stck_oprc", 75000)),
                        "high_price": float(out.get("stck_hgpr", 75500)),
                        "low_price": float(out.get("stck_lwpr", 74500)),
                        "close_price": float(out.get("stck_prpr", 75000)),
                        "volume": int(out.get("cntg_vol", 100)),
                        "change_rate": float(out.get("prdy_ctrt", 0.0)),
                    }
                elif "ticker" in data:
                    return {
                        "ticker": data.get("ticker", "005930"),
                        "open_price": float(data.get("open", 75000)),
                        "high_price": float(data.get("high", 75500)),
                        "low_price": float(data.get("low", 74500)),
                        "close_price": float(data.get("price", 75000)),
                        "volume": int(data.get("volume", 100)),
                        "change_rate": float(data.get("change_rate", 0.0)),
                    }
        except Exception as e:
            logger.debug("stream_worker.parse_debug", error=str(e), msg_snippet=raw_msg[:50])
        return None

    async def _periodic_flush(self):
        """버퍼에 축적된 1분봉 틱 데이터를 주기적으로 PostgreSQL에 벌크 인서트"""
        while self._running:
            await asyncio.sleep(self.flush_interval)
            if self.buffer:
                records_to_flush = self.buffer.copy()
                self.buffer.clear()
                try:
                    async with async_session_factory() as session:
                        entities = [
                            StockMinutePrice(
                                ticker=r["ticker"],
                                open_price=r.get("open_price", r["close_price"]),
                                high_price=r.get("high_price", r["close_price"]),
                                low_price=r.get("low_price", r["close_price"]),
                                close_price=r["close_price"],
                                volume=r.get("volume", 100),
                                change_rate=r.get("change_rate", 0.0),
                            )
                            for r in records_to_flush
                        ]
                        session.add_all(entities)
                        await session.commit()
                        logger.info(
                            "stream_worker.bulk_flushed",
                            count=len(entities),
                            tickers=list(set(r["ticker"] for r in records_to_flush)),
                        )
                except Exception as e:
                    logger.warning("stream_worker.flush_failed", error=str(e), count=len(records_to_flush))

    async def _run_mock_stream_generator(self):
        """API 키 부재 시 오프라인 테스트용 모의 실시간 틱 데이터 생성 루프"""
        tickers = self.watchlist_mgr.get_watchlist()
        logger.info("stream_worker.starting_mock_stream", tickers=tickers)

        while self._running:
            for ticker in tickers:
                base_price = 75000.0 if ticker == "005930" else 150000.0
                fluctuation = random.uniform(-0.005, 0.005)
                price = round(base_price * (1 + fluctuation), 0)
                tick = {
                    "ticker": ticker,
                    "open_price": price - 100,
                    "high_price": price + 200,
                    "low_price": price - 200,
                    "close_price": price,
                    "volume": random.randint(10, 500),
                    "change_rate": round(fluctuation * 100, 2),
                }
                self.buffer.append(tick)
            await asyncio.sleep(10.0)

    async def _run_kis_rest_poller(self, redis_client=None):
        """KIS REST API(inquire-price)를 통해 정확한 실시간 시세를 주기적으로 수집하여 DB 및 Redis에 적재"""
        while self._running:
            # PostgreSQL stock_watchlist 및 Redis에서 최신 활성 종목 동기화
            await self.watchlist_mgr.sync_from_db_and_redis()
            tickers = self.watchlist_mgr.get_watchlist()

            if not tickers:
                logger.debug("stream_worker.kis_rest_poller_idle", reason="user watchlist is empty - idle waiting")
                await asyncio.sleep(3.0)
                continue



            for ticker in tickers:
                if not self._running:
                    break
                try:
                    price_info = await self.kis_client.fetch_current_price(ticker)
                    if price_info and price_info.get("price"):
                        tick = {
                            "ticker": ticker,
                            "open_price": price_info.get("open", price_info["price"]),
                            "high_price": price_info.get("high", price_info["price"]),
                            "low_price": price_info.get("low", price_info["price"]),
                            "close_price": price_info["price"],
                            "volume": price_info.get("volume", 100),
                            "change_rate": price_info.get("changePercent", 0.0),
                        }
                        self.buffer.append(tick)
                        if redis_client:
                            try:
                                await redis_client.set(f"stock:quote:{ticker}", json.dumps(price_info))
                            except Exception:
                                pass
                        logger.info("stream_worker.kis_rest_tick_recorded", ticker=ticker, price=price_info["price"])
                except Exception as e:
                    logger.debug("stream_worker.kis_rest_poll_error", ticker=ticker, error=str(e))
                # KIS 초당 호출 제한 방어: 모의투자는 1.0초, 실전투자는 0.5초 대기
                sleep_interval = 1.0 if self.kis_client.is_paper else 0.5
                await asyncio.sleep(sleep_interval)
            # 10초 기준 주기적 시세 수집
            await asyncio.sleep(10.0)


    async def connect_and_stream(self):
        """실시간 스트림 연결 및 수신 메인 루프"""
        self._running = True
        await init_db()
        flush_task = asyncio.create_task(self._periodic_flush())

        # Redis 비동기 클라이언트 연결 (실시간 시세 인메모리 서빙용)
        redis_client = None
        try:
            import redis.asyncio as aioredis
            redis_host = self.settings.redis_host or "agent_redis"
            redis_port = self.settings.redis_port or 6379
            redis_client = aioredis.from_url(
                f"redis://{redis_host}:{redis_port}",
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("stream_worker.redis_connected", host=redis_host, port=redis_port)
        except Exception as e:
            logger.warning("stream_worker.redis_connect_failed", error=str(e))

        rest_poller_task = None
        try:
            if self.kis_client.is_configured():
                # Redis 워치리스트 매니저 연결
                if redis_client:
                    self.watchlist_mgr.set_redis(redis_client)
                    await self.watchlist_mgr.sync_from_db_and_redis()


                # KIS REST 실시간 시세 폴러 백그라운드 태스크 시작
                rest_poller_task = asyncio.create_task(self._run_kis_rest_poller(redis_client))

                approval_key = await self.kis_client.get_websocket_approval_key()
                ws_url = self.kis_client.ws_url
                logger.info("stream_worker.connecting_kis_ws", url=ws_url, has_approval_key=bool(approval_key))

                
                try:
                    async with websockets.connect(ws_url) as ws:
                        for ticker in self.watchlist_mgr.get_watchlist():
                            reg_msg = self.kis_client.get_subscription_payload(ticker, is_register=True)
                            await ws.send(reg_msg)
                            logger.info("stream_worker.subscribed_ticker", ticker=ticker)

                        while self._running:
                            raw_msg = await ws.recv()
                            parsed = self.parse_kis_tick(str(raw_msg))
                            if parsed:
                                self.buffer.append(parsed)
                                if redis_client:
                                    try:
                                        tick_ticker = parsed.get("ticker", "005930")
                                        await redis_client.set(f"stock:quote:{tick_ticker}", json.dumps(parsed))
                                    except Exception:
                                        pass
                except Exception as ws_err:
                    logger.warning("stream_worker.ws_stream_warning", error=str(ws_err))
                    # WebSocket 실패 시에도 REST Poller가 지속적으로 시세를 적재함
                    while self._running:
                        await asyncio.sleep(1.0)
            else:
                logger.info("stream_worker.no_kis_keys_using_mock_stream")
                await self._run_mock_stream_generator()
        except Exception as e:
            logger.error("stream_worker.connection_error", error=str(e))
        finally:
            self._running = False
            flush_task.cancel()
            if rest_poller_task:
                rest_poller_task.cancel()
            if redis_client:
                await redis_client.aclose()


if __name__ == "__main__":
    worker = RealtimeStreamWorker()
    asyncio.run(worker.connect_and_stream())

