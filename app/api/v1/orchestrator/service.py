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

        # 1-1. Automatically add to active watchlist so stream_worker polls this user-requested ticker
        if ticker != "generic":
            try:
                import redis.asyncio as aioredis
                r = aioredis.from_url(
                    f"redis://{settings.redis_host or 'agent_redis'}:{settings.redis_port or 6379}",
                    encoding="utf-8",
                    decode_responses=True,
                )
                raw_wl = await r.get("watchlist:active")
                wl_tickers = json.loads(raw_wl) if raw_wl else []
                if ticker not in wl_tickers:
                    wl_tickers.append(ticker)
                    await r.set("watchlist:active", json.dumps(wl_tickers), ex=3600 * 24)
                    logger.info("watchlist.auto_registered_from_user_query", ticker=ticker)
                await r.aclose()
            except Exception as e:
                logger.debug("watchlist.auto_register_skip", ticker=ticker, error=str(e))

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
                    step_results=cached_data.get("step_results"),
                    executive_metrics=cached_data.get("executive_metrics"),
                    recommendation=cached_data.get("recommendation"),
                    remote_response=cached_data.get("remote_response"),
                    is_cached=True,
                    cached_at=cached_data.get("cached_at"),
                    ttl_remaining=ttl_left if ttl_left > 0 else settings.redis_cache_ttl_seconds,
                )

        # 3. Cache Miss or Force Refresh: Execute Supervisor Pipeline
        logger.info("task.orchestrator.cache_miss", ticker=ticker, cache_key=cache_key)
        
        # Check if query is recommendation-oriented
        is_rec_query = any(w in body.message for w in ["추천", "top pick", "top 3", "유망", "스크리닝", "포트폴리오"])
        rec_data = None
        if is_rec_query and ticker == "generic":
            try:
                from agents.recommendation_agent import StockRecommendationAgent
                rec_result = await StockRecommendationAgent.generate_recommendation(body.message)
                rec_data = rec_result.model_dump()
            except Exception as e:
                logger.warning("orchestrator.recommendation_error", error=str(e))

        result = await supervisor.ainvoke(body.model_dump())

        # If recommendation markdown is generated, prepend/use it
        output_text = result.get("output", "")
        if rec_data and rec_data.get("report_markdown"):
            output_text = rec_data["report_markdown"]

        now_iso = datetime.now(timezone.utc).isoformat()
        response_data = {
            "output": output_text,
            "used_agents": result.get("used_agents", []),
            "plan": result.get("plan"),
            "step_results": result.get("step_results"),
            "executive_metrics": result.get("executive_metrics"),
            "recommendation": rec_data,
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
            step_results=response_data["step_results"],
            executive_metrics=response_data["executive_metrics"],
            recommendation=rec_data,
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
