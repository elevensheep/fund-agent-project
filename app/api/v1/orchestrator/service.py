import json
import re
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any

from agents.supervisor import SupervisorAgent
from api.v1.orchestrator.schema import InvokeRequest, InvokeResponse
from core.config import get_settings
from shared_core.cache import get_cache_manager, RedisCacheManager
from shared_core.logger import logger


class OrchestratorService:
    @staticmethod
    async def invoke(body: InvokeRequest, supervisor: SupervisorAgent) -> InvokeResponse:
        settings = get_settings()
        logger.info(
            "api.v1.orchestrator.invoke",
            message=body.message,
            thread_id=body.thread_id,
            force_refresh=body.force_refresh,
        )

        cache_mgr = get_cache_manager(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password or None,
            default_ttl=settings.redis_cache_ttl_seconds,
        )

        # 1. Extract stock ticker for structured cache key
        ticker_match = re.search(r"\b(\d{6})\b", body.message)
        ticker = ticker_match.group(1) if ticker_match else "generic"
        cache_key = RedisCacheManager.generate_key(
            "cache:supervisor:analysis",
            ticker,
            RedisCacheManager.hash_text(body.message),
        )

        # 2. Check Cache
        if not body.force_refresh and settings.enable_cache:
            cached_data = await cache_mgr.get_json(cache_key)
            if cached_data and isinstance(cached_data, dict):
                ttl_left = await cache_mgr.ttl(cache_key)
                logger.info(
                    "task.orchestrator.cache_hit",
                    ticker=ticker,
                    cache_key=cache_key,
                    ttl_remaining=ttl_left,
                )
                return InvokeResponse(
                    output=cached_data.get("output", ""),
                    used_agents=cached_data.get("used_agents", []),
                    plan=cached_data.get("plan"),
                    remote_response=cached_data.get("remote_response"),
                    is_cached=True,
                    cached_at=cached_data.get("cached_at"),
                    ttl_remaining=ttl_left if ttl_left > 0 else settings.redis_cache_ttl_seconds,
                )

        # 3. Cache Miss or Force Refresh: Execute Supervisor Pipeline
        logger.info("task.orchestrator.cache_miss", ticker=ticker, cache_key=cache_key)
        result = await supervisor.ainvoke(body.model_dump())

        now_iso = datetime.now(timezone.utc).isoformat()
        response_data = {
            "output": result.get("output", ""),
            "used_agents": result.get("used_agents", []),
            "plan": result.get("plan"),
            "remote_response": result.get("remote_response"),
            "cached_at": now_iso,
        }

        # 4. Save to Redis with TTL
        if settings.enable_cache:
            await cache_mgr.set_json(
                cache_key,
                response_data,
                ttl_seconds=settings.redis_cache_ttl_seconds,
            )
            logger.info(
                "task.orchestrator.cache_stored",
                ticker=ticker,
                cache_key=cache_key,
                ttl=settings.redis_cache_ttl_seconds,
            )

        return InvokeResponse(
            output=response_data["output"],
            used_agents=response_data["used_agents"],
            plan=response_data["plan"],
            remote_response=response_data["remote_response"],
            is_cached=False,
            cached_at=now_iso,
            ttl_remaining=settings.redis_cache_ttl_seconds,
        )

    @staticmethod
    async def stream(body: InvokeRequest, supervisor: SupervisorAgent) -> AsyncGenerator[str, None]:
        logger.info("api.v1.orchestrator.stream", message=body.message, thread_id=body.thread_id)
        async for chunk in supervisor.astream(body.model_dump()):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    @staticmethod
    async def get_info(supervisor: SupervisorAgent) -> Dict[str, Any]:
        await supervisor._ensure_agent_cards()
        return {
            "name": supervisor.name,
            "llm_provider": supervisor.llm.__class__.__name__,
            "remote_agents": supervisor.remote_agents,
            "agent_cards": supervisor.agent_cards,
        }
