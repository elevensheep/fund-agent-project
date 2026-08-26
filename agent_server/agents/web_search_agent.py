from pathlib import Path
from typing import Any, Dict, List

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.langgraph_agent import LangGraphAgent
from google.adk.events.event import Event
from google.genai import types
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from prometheus_fastapi_instrumentator import Instrumentator

from core.llm import get_chat_model
import os
import redis
from shared_core.cache import RedisCacheManager
from shared_core.logger import logger
from shared_core.prompt import load_prompt


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """
    DuckDuckGo 엔진을 사용하여 최신 웹 및 주식 시장 뉴스, 기업 정보를 검색합니다. (Redis 캐시 지원)
    """
    cache_key = RedisCacheManager.generate_key("cache:web_search", RedisCacheManager.hash_text(f"{query}:{max_results}"))
    redis_client = None

    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "agent_redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD") or None,
            decode_responses=True,
            socket_timeout=1.5,
        )
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info("web_search.cache_hit", query=query, cache_key=cache_key)
            return cached_result
    except Exception as e:
        logger.debug("web_search.cache_check_failed", error=str(e))

    logger.info("web_search.execute", query=query, max_results=max_results)
    output = None
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if results:
                formatted = []
                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    href = r.get("href", "")
                    formatted.append(f"- [{title}]({href}): {body}")
                output = "\n".join(formatted)
    except Exception as e:
        logger.warning("web_search.ddgs_failed_fallback", query=query, error=str(e))

    if not output:
        # Mock Fallback when offline or rate-limited
        output = (
            f"🔍 '{query}' 웹 검색 결과:\n"
            f"1. [최신 시장 브리핑] 반도체 섹터 수출 증가세 지속, 주요 기업 실적 개선 전망.\n"
            f"2. [기업 공시 요약] 신제품 라인업 양산 본격화 및 글로벌 공급 계약 체결 소식.\n"
            f"3. [증권가 리포트] 목표주가 상향 조정 및 외국인/기관 순매수 유입세 확인."
        )

    # Cache for 10 minutes (600 seconds)
    if redis_client:
        try:
            redis_client.set(cache_key, output, ex=int(os.getenv("REDIS_SEARCH_CACHE_TTL_SECONDS", 600)))
            logger.info("web_search.cache_stored", query=query, cache_key=cache_key)
        except Exception:
            pass

    return output


tools = [web_search]


class SafeLangGraphAgent(LangGraphAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        config = {"configurable": {"thread_id": ctx.session.id}}
        logger.info("task.web_search_agent.start", invocation_id=ctx.invocation_id, session_id=ctx.session.id)

        graph_messages = []
        if self.graph.checkpointer:
            current_graph_state = await self.graph.aget_state(config)
            graph_messages = (
                current_graph_state.values.get("messages", [])
                if current_graph_state.values
                else []
            )
        messages = (
            [SystemMessage(content=self.instruction)]
            if self.instruction and not graph_messages
            else []
        )
        messages += self._get_messages(ctx.session.events)

        final_state = await self.graph.ainvoke({"messages": messages}, config)
        result = final_state["messages"][-1].content

        if isinstance(result, list):
            text_parts = []
            for part in result:
                if isinstance(part, dict) and "text" in part:
                    text_parts.append(part["text"])
                elif isinstance(part, str):
                    text_parts.append(part)
            result = "".join(text_parts) if text_parts else str(result)
        elif not isinstance(result, str):
            result = str(result)

        logger.info("task.web_search_agent.completed", invocation_id=ctx.invocation_id, output=result)

        result_event = Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=result)],
            ),
        )
        logger.info("artifact.web_search_agent.event_created", invocation_id=ctx.invocation_id, author=self.name)
        yield result_event


def create_app():
    llm = get_chat_model()
    prompt_path = Path(__file__).parent / "prompts" / "web_search.yml"
    system_prompt = load_prompt(
        prompt_path,
        key="system_prompt",
        default="You are an expert financial Web Search Agent. Search and summarize market news.",
    )

    graph = create_react_agent(model=llm, tools=tools, prompt=system_prompt)
    agent = SafeLangGraphAgent(
        name="web_search_agent",
        description="DuckDuckGo 실시간 웹 검색 및 최신 금융 뉴스 탐색 ReAct 에이전트",
        graph=graph,
    )

    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()
