import asyncio
import json
import os
import re
import urllib.request
from typing import Any, Dict, List, Optional
import asyncpg
from shared_core.db_stock_tool import STOCK_MASTER
from shared_core.logger import logger

KIND_URL = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"

KNOWN_ALIASES: Dict[str, List[str]] = {
    "삼성전자": ["삼전", "삼성", "samsung"],
    "SK하이닉스": ["하이닉스", "하닉", "hynix"],
    "현대자동차": ["현대차", "현차", "hyundai"],
    "LG에너지솔루션": ["엔솔", "LG엔솔", "엘지에너지솔루션"],
    "POSCO홀딩스": ["포스코홀딩스", "포스코", "posco"],
    "포스코퓨처엠": ["퓨처엠", "포스코케미칼"],
    "한화에어로스페이스": ["한화에어로", "에어로스페이스", "에어로"],
    "삼성바이오로직스": ["삼바", "로직스"],
    "두산에너빌리티": ["에너빌리티", "두산중공업"],
    "HD현대중공업": ["현대중공업"],
    "HD현대일렉트릭": ["현대일렉트릭", "현대일렉"],
    "한화오션": ["대우조선해양"],
    "삼양식품": ["불닭", "삼양"],
    "카카오뱅크": ["카뱅"],
    "카카오페이": ["카페"],
    "에코프로머티": ["머티"],
}


def fetch_krx_stock_list() -> List[Dict[str, Any]]:
    """
    한국거래소(KRX KIND)로부터 최신 KOSPI 및 KOSDAQ 상장 주식 마스터(2,600+ 종목)를 수집합니다.
    """
    stocks: List[Dict[str, Any]] = []
    req = urllib.request.Request(
        KIND_URL,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    try:
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            html = resp.read().decode("cp949", errors="ignore")
            rows = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)
            for r in rows[1:]:
                cols = [
                    re.sub(r"<.*?>", "", c).strip()
                    for c in re.findall(r"<td.*?>(.*?)</td>", r, re.DOTALL)
                ]
                if len(cols) >= 4:
                    name = cols[0]
                    market_raw = cols[1]
                    code = cols[2].zfill(6)
                    sector = cols[3]

                    if market_raw == "유가":
                        market = "KOSPI"
                    elif market_raw == "코스닥":
                        market = "KOSDAQ"
                    else:
                        continue

                    if re.match(r"^\d{6}$", code):
                        aliases = [name, code]
                        for k, alias_list in KNOWN_ALIASES.items():
                            if k in name or name in k:
                                aliases.extend(alias_list)

                        stocks.append({
                            "ticker": code,
                            "name": name,
                            "market": market,
                            "sector": sector or "주요 상장기업",
                            "aliases": list(set(aliases)),
                        })
        logger.info("stock_seeder.krx_kind_fetched", count=len(stocks))
    except Exception as e:
        logger.warning("stock_seeder.krx_kind_fetch_error", error=str(e))

    # KIND 수집 실패 시 또는 추가 보완용 STOCK_MASTER 병합
    existing_tickers = {s["ticker"] for s in stocks}
    for ticker, info in STOCK_MASTER.items():
        if ticker not in existing_tickers:
            stocks.append({
                "ticker": ticker,
                "name": info["name"],
                "market": info.get("market", "KOSPI"),
                "sector": info.get("sector", "대표 우량기업"),
                "aliases": info.get("aliases", [info["name"], ticker]),
            })

    return stocks


async def reset_and_seed_stock_database(reset_legacy: bool = False) -> Dict[str, Any]:
    """
    PostgreSQL 데이터베이스의 레거시 데이터를 정리하고 전체 KRX 상장사 마스터 데이터를 시딩합니다.
    - reset_legacy=True: 기존 stock_master_info, stock_watchlist, stock_daily_metrics, stock_minute_prices 초기화
    """
    pg_host = os.getenv("POSTGRES_HOST", "agent_postgres")
    pg_port = int(os.getenv("POSTGRES_PORT", 5432))
    pg_user = os.getenv("POSTGRES_USER", "postgres")
    pg_pass = os.getenv("POSTGRES_PASSWORD", "postgres_secure_pw")
    pg_db = os.getenv("POSTGRES_DB", "agent_stock_db")

    conn = await asyncpg.connect(
        host=pg_host,
        port=pg_port,
        user=pg_user,
        password=pg_pass,
        database=pg_db,
        timeout=10.0,
    )

    try:
        if reset_legacy:
            logger.info("stock_seeder.wiping_legacy_tables")
            await conn.execute("""
                DROP TABLE IF EXISTS stock_minute_prices CASCADE;
                DROP TABLE IF EXISTS stock_daily_metrics CASCADE;
                DROP TABLE IF EXISTS stock_watchlist CASCADE;
                DROP TABLE IF EXISTS stock_master_info CASCADE;
            """)

        # 1. 테이블 스키마 생성
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
            CREATE INDEX IF NOT EXISTS idx_stock_master_name ON stock_master_info (name);
            CREATE INDEX IF NOT EXISTS idx_stock_master_market ON stock_master_info (market);

            CREATE TABLE IF NOT EXISTS stock_watchlist (
                ticker VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                market VARCHAR(20) DEFAULT 'KOSPI',
                sector VARCHAR(100) DEFAULT '',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS stock_daily_metrics (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(20) NOT NULL,
                close_price DOUBLE PRECISION NOT NULL,
                sma_20 DOUBLE PRECISION,
                sentiment VARCHAR(20),
                summary TEXT,
                impact_score INTEGER DEFAULT 5,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_stock_daily_ticker_date ON stock_daily_metrics (ticker, created_at);

            CREATE TABLE IF NOT EXISTS stock_minute_prices (
                id BIGSERIAL PRIMARY KEY,
                ticker VARCHAR(20) NOT NULL,
                open_price DOUBLE PRECISION DEFAULT 0.0,
                high_price DOUBLE PRECISION DEFAULT 0.0,
                low_price DOUBLE PRECISION DEFAULT 0.0,
                close_price DOUBLE PRECISION NOT NULL,
                volume BIGINT DEFAULT 0,
                change_rate DOUBLE PRECISION DEFAULT 0.0,
                recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_stock_minute_ticker_time ON stock_minute_prices (ticker, recorded_at);
        """)

        # 2. KRX 주식 마스터 수집
        stock_list = fetch_krx_stock_list()

        # 3. Bulk Insert (배치 적재)
        records = [
            (
                s["ticker"],
                s["name"],
                s["market"],
                s.get("sector", "주요 상장기업"),
                0.0,
                s.get("aliases", [s["name"], s["ticker"]]),
            )
            for s in stock_list
        ]

        await conn.executemany(
            """
            INSERT INTO stock_master_info (ticker, name, market, sector, default_price, aliases)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (ticker) DO UPDATE
            SET name = EXCLUDED.name,
                market = EXCLUDED.market,
                sector = EXCLUDED.sector,
                aliases = EXCLUDED.aliases;
            """,
            records,
        )

        # 4. Redis 캐시 초기화 (reset_legacy 시)
        if reset_legacy:
            try:
                import redis.asyncio as aioredis
                r_host = os.getenv("REDIS_HOST", "agent_redis")
                r_port = int(os.getenv("REDIS_PORT", 6379))
                r = aioredis.from_url(f"redis://{r_host}:{r_port}", decode_responses=True)
                await r.delete("watchlist:active")
                # Remove stock quotes
                keys = await r.keys("stock:quote:*")
                if keys:
                    await r.delete(*keys)
                await r.aclose()
                logger.info("stock_seeder.redis_cleared", quote_keys_removed=len(keys))
            except Exception as e:
                logger.debug("stock_seeder.redis_clean_skip", error=str(e))

        total_count = await conn.fetchval("SELECT count(*) FROM stock_master_info;")
        kospi_count = await conn.fetchval("SELECT count(*) FROM stock_master_info WHERE market = 'KOSPI';")
        kosdaq_count = await conn.fetchval("SELECT count(*) FROM stock_master_info WHERE market = 'KOSDAQ';")

        logger.info(
            "stock_seeder.complete",
            total=total_count,
            kospi=kospi_count,
            kosdaq=kosdaq_count,
        )

        return {
            "status": "success",
            "total_stocks": total_count,
            "kospi": kospi_count,
            "kosdaq": kosdaq_count,
        }
    finally:
        await conn.close()


async def ensure_krx_stock_master_seeded() -> None:
    """앱 시작 시 stock_master_info 테이블이 비어있거나 부족하면 자동 시딩 실행"""
    try:
        pg_host = os.getenv("POSTGRES_HOST", "agent_postgres")
        pg_port = int(os.getenv("POSTGRES_PORT", 5432))
        pg_user = os.getenv("POSTGRES_USER", "postgres")
        pg_pass = os.getenv("POSTGRES_PASSWORD", "postgres_secure_pw")
        pg_db = os.getenv("POSTGRES_DB", "agent_stock_db")

        conn = await asyncpg.connect(
            host=pg_host,
            port=pg_port,
            user=pg_user,
            password=pg_pass,
            database=pg_db,
            timeout=2.5,
        )
        try:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'stock_master_info'
                );
            """)
            count = 0
            if exists:
                count = await conn.fetchval("SELECT count(*) FROM stock_master_info;")
            if count < 500:
                logger.info("stock_seeder.auto_seeding_triggered", current_count=count)
                await reset_and_seed_stock_database(reset_legacy=False)
        finally:
            await conn.close()
    except Exception as e:
        logger.warning("stock_seeder.auto_seed_check_failed", error=str(e))
