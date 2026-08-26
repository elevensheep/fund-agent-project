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
            await asyncio.sleep(2.0)

    async def connect_and_stream(self):
        """실시간 스트림 연결 및 수신 메인 루프"""
        self._running = True
        await init_db()
        flush_task = asyncio.create_task(self._periodic_flush())

        try:
            if self.kis_client.is_configured():
                approval_key = await self.kis_client.get_websocket_approval_key()
                ws_url = self.kis_client.ws_url
                logger.info("stream_worker.connecting_kis_ws", url=ws_url, has_approval_key=bool(approval_key))
                
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
            else:
                logger.info("stream_worker.no_kis_keys_using_mock_stream")
                await self._run_mock_stream_generator()
        except Exception as e:
            logger.error("stream_worker.connection_error", error=str(e))
        finally:
            self._running = False
            flush_task.cancel()


if __name__ == "__main__":
    worker = RealtimeStreamWorker()
    asyncio.run(worker.connect_and_stream())
