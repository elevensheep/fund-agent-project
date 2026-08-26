import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from core.config import get_settings
from core.models import Base
from shared_core.logger import logger

settings = get_settings()

def _get_database_url() -> str:
    # Check for direct DATABASE_URL env var
    env_db_url = os.getenv("DATABASE_URL")
    if env_db_url:
        return env_db_url

    # Construct PostgreSQL async URL
    host = settings.postgres_host
    port = settings.postgres_port
    user = settings.postgres_user
    password = settings.postgres_password
    dbname = settings.postgres_db

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"


def create_engine_and_session() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    db_url = _get_database_url()
    try:
        if "postgresql" in db_url:
            engine = create_async_engine(
                db_url,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_pre_ping=True,
            )
        else:
            engine = create_async_engine(db_url)
    except Exception as e:
        logger.warning("database.engine_creation_fallback", error=str(e))
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine, session_factory


engine, async_session_factory = create_engine_and_session()


async def init_db() -> None:
    """데이터베이스 테이블 초기화 (테스트 및 시작 시 호출)"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database.initialized", tables=list(Base.metadata.tables.keys()))
    except Exception as e:
        logger.warning("database.init_failed", error=str(e))


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """비동기 DB 세션 컨텍스트 매니저"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
