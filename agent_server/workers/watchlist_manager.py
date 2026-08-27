import asyncio
import json
import os
from typing import List, Optional, Set
import asyncpg
import redis.asyncio as aioredis
from shared_core.logger import logger

REDIS_WATCHLIST_KEY = "watchlist:active"
REDIS_WATCHLIST_TTL = 3600 * 24  # 24시간


class WatchlistManager:
    """
    PostgreSQL `stock_watchlist` 테이블 및 Redis 기반 온디맨드 동적 워치리스트 관리자.
    기본적으로 워치리스트는 비어 있으며, 사용자가 프론트엔드/API에서 종목을 선택하여
    DB `stock_watchlist`에 등록하거나 검색했을 때만 stream_worker가 해당 종목을 폴링합니다.
    """

    def __init__(
        self,
        initial_tickers: Optional[List[str]] = None,
        redis_client: Optional[aioredis.Redis] = None,
    ):
        self._local_watchlist: Set[str] = set(initial_tickers or [])
        self._redis: Optional[aioredis.Redis] = redis_client

    def set_redis(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client

    def get_watchlist(self) -> List[str]:
        return sorted(self._local_watchlist)

    def add_ticker(self, ticker: str) -> None:
        if ticker not in self._local_watchlist and len(self._local_watchlist) < 50:
            self._local_watchlist.add(ticker)
            logger.info("watchlist.added_local", ticker=ticker, total=len(self._local_watchlist))

    def remove_ticker(self, ticker: str) -> None:
        self._local_watchlist.discard(ticker)
        logger.info("watchlist.removed_local", ticker=ticker, total=len(self._local_watchlist))

    async def sync_from_db_and_redis(self) -> None:
        """PostgreSQL `stock_watchlist` (is_active=TRUE) 및 Redis에서 활성 종목 동기화"""
        active_set: Set[str] = set()

        # 1. PostgreSQL stock_watchlist 조회
        try:
            conn = await asyncpg.connect(
                host=os.getenv("POSTGRES_HOST", "agent_postgres"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres_secure_pw"),
                database=os.getenv("POSTGRES_DB", "agent_stock_db"),
                timeout=2.0,
            )
            rows = await conn.fetch("SELECT ticker FROM stock_watchlist WHERE is_active = TRUE")
            for r in rows:
                active_set.add(r["ticker"])
            await conn.close()
        except Exception as e:
            logger.debug("watchlist.pg_sync_debug", error=str(e))

        # 2. Redis watchlist:active 조회
        if self._redis:
            try:
                raw = await self._redis.get(REDIS_WATCHLIST_KEY)
                if raw:
                    tickers: List[str] = json.loads(raw)
                    active_set.update(tickers)
            except Exception as e:
                logger.debug("watchlist.redis_sync_debug", error=str(e))

        self._local_watchlist = active_set


async def register_ticker_to_db_and_redis(
    ticker: str,
    name: str = "",
    market: str = "KOSPI",
    sector: str = "",
    redis_url: str = "redis://agent_redis:6379",
) -> None:
    """사용자가 종목을 선택했을 때 PostgreSQL `stock_watchlist`와 Redis에 등록"""
    # 1. PostgreSQL DB Upsert
    try:
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "agent_postgres"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres_secure_pw"),
            database=os.getenv("POSTGRES_DB", "agent_stock_db"),
            timeout=2.0,
        )
        await conn.execute(
            """
            INSERT INTO stock_watchlist (ticker, name, market, sector, is_active, updated_at)
            VALUES ($1, $2, $3, $4, TRUE, NOW())
            ON CONFLICT (ticker) DO UPDATE
            SET is_active = TRUE, updated_at = NOW()
            """,
            ticker, name or ticker, market, sector
        )
        await conn.close()
        logger.info("watchlist.registered_pg", ticker=ticker, name=name)
    except Exception as e:
        logger.warning("watchlist.pg_register_error", ticker=ticker, error=str(e))

    # 2. Redis Register
    try:
        r = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        raw = await r.get(REDIS_WATCHLIST_KEY)
        tickers: List[str] = json.loads(raw) if raw else []
        if ticker not in tickers:
            tickers.append(ticker)
        await r.set(REDIS_WATCHLIST_KEY, json.dumps(tickers), ex=REDIS_WATCHLIST_TTL)
        await r.aclose()
        logger.info("watchlist.registered_redis", ticker=ticker)
    except Exception as e:
        logger.warning("watchlist.redis_register_error", ticker=ticker, error=str(e))
