import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncpg
from fastapi import APIRouter, Body, HTTPException, Query
import redis.asyncio as aioredis
from core.config import get_settings
from shared_core.db_stock_tool import STOCK_MASTER, fetch_latest_stock_price, fetch_stock_candles
from shared_core.logger import logger

router = APIRouter(prefix="/stock", tags=["stock"])
settings = get_settings()

STOCK_NAMES = {k: {"name": v["name"], "market": v.get("market", "KOSPI")} for k, v in STOCK_MASTER.items()}
REDIS_WATCHLIST_KEY = "watchlist:active"
REDIS_WATCHLIST_TTL = 3600 * 24  # 24시간


def get_redis_url() -> str:
    host = settings.redis_host or "agent_redis"
    port = settings.redis_port or 6379
    return f"redis://{host}:{port}"


async def get_db_connection():
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "agent_postgres"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres_secure_pw"),
        database=os.getenv("POSTGRES_DB", "agent_stock_db"),
        timeout=3.0,
    )


# ─── 1. 종목 검색 엔드포인트 (Stock Resolution Search API) ────────────────────

@router.get("/search")
async def search_stocks(
    query: str = Query(..., min_length=1, description="종목명, 티커코드, 섹터 등 검색어"),
    limit: int = Query(10, ge=1, le=50, description="최대 반환 개수"),
) -> List[Dict[str, Any]]:
    """
    [Orchestrator Search API]
    PostgreSQL `stock_master_info` 및 사전 데이터베이스를 조회하여
    사용자 입력어와 매칭되는 KIS 국내 상장 종목 목록을 반환합니다.
    (DB에 없는 신규 종목의 경우 LLM 기반 KRX 종목 식별 및 자동 적재 수행)
    """
    clean_q = query.strip()
    results: List[Dict[str, Any]] = []

    # 1. PostgreSQL DB 조회
    try:
        conn = await get_db_connection()
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_master_info (
                ticker VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                market VARCHAR(20) DEFAULT 'KOSPI',
                sector VARCHAR(100) DEFAULT '주요 상장기업',
                default_price DOUBLE PRECISION DEFAULT 0.0,
                aliases TEXT[] DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        search_pattern = f"%{clean_q}%"
        rows = await conn.fetch(
            """
            SELECT ticker, name, market, sector, default_price
            FROM stock_master_info
            WHERE ticker ILIKE $1 
               OR name ILIKE $1 
               OR sector ILIKE $1
               OR $2 = ANY(aliases)
            ORDER BY 
               CASE 
                 WHEN ticker = $2 THEN 1
                 WHEN name = $2 THEN 2
                 WHEN name ILIKE $1 THEN 3
                 ELSE 4 
               END,
               name ASC
            LIMIT $3
            """,
            search_pattern, clean_q, limit
        )
        await conn.close()

        for r in rows:
            results.append({
                "ticker": r["ticker"],
                "name": r["name"],
                "market": r["market"],
                "sector": r["sector"] or "주요 우량기업",
                "default_price": float(r["default_price"] or 0.0),
            })
    except Exception as e:
        logger.warning("stock_search.db_query_fallback", query=clean_q, error=str(e))

    # 2. In-Memory STOCK_MASTER Fallback (DB 에러 또는 결과 부족 시)
    if not results:
        q_lower = clean_q.lower()
        for ticker, info in STOCK_MASTER.items():
            name = info["name"]
            sector = info.get("sector", "대표 우량기업")
            aliases = [a.lower() for a in info.get("aliases", [])]
            if (
                q_lower in ticker
                or q_lower in name.lower()
                or q_lower in sector.lower()
                or any(q_lower in a for a in aliases)
            ):
                results.append({
                    "ticker": ticker,
                    "name": name,
                    "market": info.get("market", "KOSPI"),
                    "sector": sector,
                    "default_price": float(info.get("default_price", 0.0)),
                })
                if len(results) >= limit:
                    break

    # 3. Dynamic LLM KRX Resolution Fallback (DB 및 사전에 없는 KOSPI/KOSDAQ 신규 상장사)
    if not results and len(clean_q) >= 2:
        try:
            from core.llm import LLMRegistry
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = LLMRegistry.get_default()
            system_msg = SystemMessage(
                content=(
                    "You are an expert Korean Stock Market (KRX - KOSPI/KOSDAQ) stock resolution engine. "
                    "Given the search term, identify if there is any publicly listed Korean company matching it. "
                    "Respond ONLY with a valid JSON object in this exact format:\n"
                    '{"found": true, "ticker": "003230", "name": "삼양식품", "market": "KOSPI", "sector": "음식료품"}\n'
                    'If no specific Korean listed company is found, return:\n'
                    '{"found": false, "ticker": "", "name": "", "market": "", "sector": ""}'
                )
            )
            resp = await llm.ainvoke([system_msg, HumanMessage(content=f"검색어: '{clean_q}'")])
            content = resp.content if isinstance(resp.content, str) else str(resp.content)
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                if data.get("found") and data.get("ticker") and len(str(data["ticker"]).strip()) == 6 and str(data["ticker"]).strip().isdigit():
                    t = str(data["ticker"]).strip()
                    n = data.get("name") or t
                    m = data.get("market") or ("KOSPI" if not t.startswith("2") else "KOSDAQ")
                    s = data.get("sector") or "상장기업"

                    # DB에 자동 적재
                    try:
                        conn = await get_db_connection()
                        await conn.execute("""
                            INSERT INTO stock_master_info (ticker, name, market, sector, aliases)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (ticker) DO UPDATE SET name = $2, market = $3, sector = $4;
                        """, t, n, m, s, [n, t])
                        await conn.close()
                    except Exception:
                        pass

                    results.append({
                        "ticker": t,
                        "name": n,
                        "market": m,
                        "sector": s,
                        "default_price": 0.0,
                    })
        except Exception as e:
            logger.warning("stock_search.llm_fallback_error", query=clean_q, error=str(e))

    return results


# ─── 2. 온디맨드 Watchlist CRUD API (사용자 선택 시 stream_worker 트리거) ─────

@router.get("/watchlist")
async def get_active_watchlist() -> List[Dict[str, Any]]:
    """
    [Watchlist API] 현재 사용자가 선택하여 활성화된(is_active=TRUE) 종목 목록을 반환합니다.
    """
    items: List[Dict[str, Any]] = []
    try:
        conn = await get_db_connection()
        rows = await conn.fetch(
            """
            SELECT ticker, name, market, sector, is_active, created_at, updated_at
            FROM stock_watchlist
            WHERE is_active = TRUE
            ORDER BY updated_at DESC
            """
        )
        await conn.close()
        for r in rows:
            items.append({
                "ticker": r["ticker"],
                "name": r["name"],
                "market": r["market"],
                "sector": r["sector"],
                "isActive": r["is_active"],
                "updatedAt": r["updated_at"].isoformat() if r["updated_at"] else "",
            })
    except Exception as e:
        logger.debug("get_watchlist.db_skip", error=str(e))

    return items


@router.post("/watchlist")
async def add_to_watchlist(
    ticker: str = Body(..., embed=True, description="추가할 6자리 종목 코드"),
    name: Optional[str] = Body(None, embed=True),
) -> Dict[str, Any]:
    """
    [Watchlist API] 사용자가 종목을 선택했을 때 DB 및 Redis에 등록하여
    stream_worker의 실시간 KIS 틱 폴링을 즉시 시작하도록 트리거합니다.
    """
    stock_meta = STOCK_MASTER.get(ticker, {"name": name or ticker, "market": "KOSPI", "sector": "우량기업"})
    stock_name = name or stock_meta["name"]
    market = stock_meta.get("market", "KOSPI")
    sector = stock_meta.get("sector", "")

    # 1. PostgreSQL DB Upsert
    try:
        conn = await get_db_connection()
        await conn.execute(
            """
            INSERT INTO stock_watchlist (ticker, name, market, sector, is_active, updated_at)
            VALUES ($1, $2, $3, $4, TRUE, NOW())
            ON CONFLICT (ticker) DO UPDATE
            SET is_active = TRUE, updated_at = NOW()
            """,
            ticker, stock_name, market, sector
        )
        await conn.close()
    except Exception as e:
        logger.warning("add_watchlist.db_error", ticker=ticker, error=str(e))

    # 2. Redis Watchlist 동기화
    try:
        client = aioredis.from_url(get_redis_url(), encoding="utf-8", decode_responses=True)
        raw = await client.get(REDIS_WATCHLIST_KEY)
        active_list = json.loads(raw) if raw else []
        if ticker not in active_list:
            active_list.append(ticker)
        await client.set(REDIS_WATCHLIST_KEY, json.dumps(active_list), ex=REDIS_WATCHLIST_TTL)
        await client.aclose()
    except Exception as e:
        logger.warning("add_watchlist.redis_error", ticker=ticker, error=str(e))

    logger.info("watchlist.user_selected_stock_polling_triggered", ticker=ticker, name=stock_name)
    return {
        "status": "success",
        "ticker": ticker,
        "name": stock_name,
        "message": f"'{stock_name}({ticker})' 종목이 워치리스트에 등록되어 실시간 데이터 수집이 시작되었습니다.",
    }


@router.delete("/watchlist/{ticker}")
async def remove_from_watchlist(ticker: str) -> Dict[str, Any]:
    """
    [Watchlist API] 사용자가 워치리스트에서 해제 시 DB `is_active=FALSE` 처리 및 Redis 제거
    """
    try:
        conn = await get_db_connection()
        await conn.execute(
            "UPDATE stock_watchlist SET is_active = FALSE, updated_at = NOW() WHERE ticker = $1",
            ticker
        )
        await conn.close()
    except Exception as e:
        logger.warning("delete_watchlist.db_error", ticker=ticker, error=str(e))

    try:
        client = aioredis.from_url(get_redis_url(), encoding="utf-8", decode_responses=True)
        raw = await client.get(REDIS_WATCHLIST_KEY)
        active_list = json.loads(raw) if raw else []
        if ticker in active_list:
            active_list.remove(ticker)
        await client.set(REDIS_WATCHLIST_KEY, json.dumps(active_list), ex=REDIS_WATCHLIST_TTL)
        await client.aclose()
    except Exception as e:
        logger.warning("delete_watchlist.redis_error", ticker=ticker, error=str(e))

    return {"status": "success", "ticker": ticker}


# ─── 3. 실시간 쿼트 조회 API ──────────────────────────────────────────────────

@router.get("/quote")
async def get_realtime_quote(
    ticker: str = Query("005930", description="6자리 종목 코드"),
) -> Dict[str, Any]:
    """
    Redis In-Memory 캐시(stream_worker 실시간 적재) 및 KIS 공용 툴로부터
    최신 실시간 시세 및 틱 정보를 조회하여 반환합니다.
    """
    meta = STOCK_MASTER.get(ticker, {"name": ticker, "market": "KOSPI"})
    
    # 1. Redis 실시간 쿼트 캐시 조회
    try:
        client = aioredis.from_url(get_redis_url(), encoding="utf-8", decode_responses=True)
        raw_tick = await client.get(f"stock:quote:{ticker}")
        await client.aclose()

        if raw_tick:
            tick_data = json.loads(raw_tick)
            p = float(tick_data.get("price") or tick_data.get("close_price") or 0)
            if p > 0:
                open_p = float(tick_data.get("open") or tick_data.get("open_price") or p)
                high_p = float(tick_data.get("high") or tick_data.get("high_price") or p)
                low_p = float(tick_data.get("low") or tick_data.get("low_price") or p)
                vol = int(tick_data.get("volume", 0))
                change_pct = float(tick_data.get("changePercent") or tick_data.get("change_rate") or 0.0)
                diff = round(p - open_p, 2)
                return {
                    "ticker": ticker,
                    "name": meta["name"],
                    "market": meta.get("market", "KOSPI"),
                    "price": p,
                    "change": diff,
                    "changePercent": change_pct,
                    "open": open_p,
                    "high": high_p,
                    "low": low_p,
                    "volume": vol,
                    "updatedAt": tick_data.get("recorded_at") or tick_data.get("updatedAt") or datetime.now().strftime("%H:%M:%S"),
                    "source": "redis_live",
                }
    except Exception as e:
        logger.debug("get_quote.redis_skip", ticker=ticker, error=str(e))

    # 2. 공용 DB Tool 실시간 KIS 직접 조회
    latest = fetch_latest_stock_price(ticker)
    p = latest["price"]
    open_p = latest["open_price"]
    return {
        "ticker": ticker,
        "name": meta["name"],
        "market": meta.get("market", "KOSPI"),
        "price": p,
        "change": round(p - open_p, 2),
        "changePercent": latest["change_rate"],
        "open": open_p,
        "high": latest["high_price"],
        "low": latest["low_price"],
        "volume": latest["volume"],
        "updatedAt": latest.get("recorded_at") or datetime.now().strftime("%H:%M:%S"),
        "source": latest.get("source", "db_tool"),
    }


# ─── 4. 주가 캔들 차트(OHLCV) 조회 API ───────────────────────────────────────

@router.get("/candles")
async def get_stock_candles(
    ticker: str = Query("005930", description="6자리 종목 코드"),
    timeframe: str = Query("1D", description="시간 프레임: '1D' (일봉), '1M' (분봉), '1W' (주봉)"),
    count: int = Query(60, ge=1, le=500, description="반환할 캔들 개수"),
) -> Dict[str, Any]:
    """
    [Candles API] KIS Open API 일봉 및 PostgreSQL `stock_minute_prices` 분봉 데이터를 연동하여
    실제 주가 캔들(OHLCV) 및 SMA 20/60 이동평균선을 반환합니다.
    (과거 데이터가 없는 신규 종목의 경우 가짜 데이터를 날조하지 않고 is_empty: True 반환)
    """
    import asyncio
    return await asyncio.to_thread(fetch_stock_candles, ticker, count, timeframe)

