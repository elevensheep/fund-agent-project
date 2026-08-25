from pathlib import Path

from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.langgraph_agent import LangGraphAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.events.event import Event
from google.genai import types
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from prometheus_fastapi_instrumentator import Instrumentator

from core.config import get_settings
from core.llm import LLMRegistry, ProviderName
from shared_core.logger import logger, setup_logger
from shared_core.prompt import load_prompt


# ── 도구(Tools) 정의 ─────────────────────────────────────────────────────────

@tool
def add_numbers(a: float, b: float) -> float:
    """두 숫자를 더합니다."""
    logger.info("langchain_agent.tool_executed", tool="add_numbers", a=a, b=b)
    return a + b


@tool
def get_weather_info(city: str) -> str:
    """지정된 도시의 날씨 정보를 조회합니다."""
    logger.info("langchain_agent.tool_executed", tool="get_weather_info", city=city)
    return f"{city}의 현재 날씨는 맑음(22°C)입니다."


tools = [add_numbers, get_weather_info]


# ── A2A 앱 빌더 ───────────────────────────────────────────────────────────────

class SafeLangGraphAgent(LangGraphAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        config = {'configurable': {'thread_id': ctx.session.id}}
        logger.info("task.langchain_agent.start", invocation_id=ctx.invocation_id, session_id=ctx.session.id)
        
        graph_messages = []
        if self.graph.checkpointer:
            current_graph_state = await self.graph.aget_state(config)
            graph_messages = (
                current_graph_state.values.get('messages', [])
                if current_graph_state.values
                else []
            )
        messages = (
            [SystemMessage(content=self.instruction)]
            if self.instruction and not graph_messages
            else []
        )
        messages += self._get_messages(ctx.session.events)
        logger.info("task.langchain_agent.message_processing", messages=[getattr(m, 'content', str(m)) for m in messages])

        final_state = await self.graph.ainvoke({'messages': messages}, config)
        result = final_state['messages'][-1].content

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

        logger.info("task.langchain_agent.completed", invocation_id=ctx.invocation_id, output=result)

        result_event = Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(
                role='model',
                parts=[types.Part.from_text(text=result)],
            ),
        )
        logger.info("artifact.langchain_agent.event_created", invocation_id=ctx.invocation_id, author=self.name, result=result)
        yield result_event


def _build_a2a_app(llm):
    """LLM을 받아 LangGraphAgent → A2A Starlette 앱을 생성합니다."""
    prompt_path = Path(__file__).parent / "prompts" / "langchain.yml"
    system_prompt = load_prompt(prompt_path, key="system_prompt", default="You are a helpful assistant.")

    graph = create_react_agent(model=llm, tools=tools, prompt=system_prompt)
    agent = SafeLangGraphAgent(
        name="langchain_agent",
        description="LangChain ReAct 에이전트 예제 (도구: 숫자 더하기, 날씨 조회)",
        graph=graph,
    )
    return to_a2a(agent)


def _create_app():
    settings = get_settings()
    setup_logger(settings.log_level)
    logger.info("langchain_agent.startup", name=settings.app_name)

    LLMRegistry.initialize_all(settings)

    # LLM 선택: openai > anthropic > google > mock fallback
    llm = None
    providers: tuple[ProviderName, ...] = ("openai", "anthropic", "google")
    for provider in providers:
        try:
            llm = LLMRegistry.get(provider)
            logger.info("langchain_agent.llm_selected", provider=provider)
            break
        except KeyError:
            continue

    if llm is None:
        logger.warning("langchain_agent.no_llm", message="No API key found. Using mock LLM.")
        llm = FakeMessagesListChatModel(
            responses=[AIMessage(content="[Mock] API Key가 설정되지 않았습니다. .env에 키를 설정해주세요.")]
        )

    a2a_app = _build_a2a_app(llm)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    logger.info("langchain_agent.ready", available_llms=LLMRegistry.available())
    
    return a2a_app

# ── uvicorn entry point ───────────────────────────────────────────────────────
app = _create_app()
