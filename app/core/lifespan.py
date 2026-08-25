from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx

from core.mcp_client import fetch_all_agent_cards
from core.config import get_settings
from core.llm import LLMRegistry
from agents.factory import AgentFactory
from shared_core.logger import logger, setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    settings = get_settings()

    setup_logger(settings.log_level)
    logger.info("app.startup", name=settings.app_name, debug=settings.debug)

    # 1. LLM Registry 초기화
    LLMRegistry.initialize_all(settings)
    app.state.llm_registry = LLMRegistry

    # 2. HTTP 클라이언트 생성 (Remote A2A Agent 호출용)
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )

    # 3. 단일 Supervisor Agent 조립 및 등록
    app.state.supervisor = AgentFactory.create_supervisor(
        settings=settings,
        http_client=app.state.http_client,
    )

    app.state.a2a_registry = settings.a2a_agents

    logger.info(
        "app.ready",
        supervisor=app.state.supervisor.name,
        available_llms=LLMRegistry.available(),
        mcp_server_url=settings.mcp_server_url,
    )

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("app.shutdown")
    await app.state.http_client.aclose()
    LLMRegistry.shutdown()
