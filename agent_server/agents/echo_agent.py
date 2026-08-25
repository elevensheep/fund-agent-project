import operator
from pathlib import Path
from typing import Annotated, Any, Dict
from typing_extensions import TypedDict

from google.adk.agents.langgraph_agent import LangGraphAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from prometheus_fastapi_instrumentator import Instrumentator

from shared_core.logger import logger
from shared_core.prompt import load_prompt


class State(TypedDict):
    messages: Annotated[list, operator.add]


def _extract_content(msg: Any) -> str:
    """메시지 객체로부터 텍스트 내용을 안전하게 추출합니다."""
    if isinstance(msg, dict):
        return str(msg.get("content", msg))
    if isinstance(msg, BaseMessage):
        content = msg.content
        if isinstance(content, list):
            return "".join(
                part.get("text", str(part)) if isinstance(part, dict) else str(part)
                for part in content
            )
        return str(content)
    return getattr(msg, "content", str(msg))


def echo_node(state: State) -> Dict[str, list]:
    """Echo 에이전트 그래프 노드: 수신한 메시지에 템플릿을 적용하여 반환합니다."""
    prompt_path = Path(__file__).parent / "prompts" / "echo.yml"
    echo_template = load_prompt(prompt_path, key="echo_template", default="[Echo] {content}")

    messages = state.get("messages", [])
    content = _extract_content(messages[-1]) if messages else ""

    logger.info("task.echo_agent.received_message", message=content)
    output_text = echo_template.format(content=content)
    logger.info("task.echo_agent.completed", output=output_text)
    logger.info("artifact.echo_agent.message_created", content=output_text)

    return {"messages": [AIMessage(content=output_text)]}


def create_echo_app():
    """LangGraph 기반 Echo Agent 및 A2A FastAPI/Starlette 애플리케이션을 빌드합니다."""
    graph_builder = StateGraph(State)
    graph_builder.add_node("echo", echo_node)
    graph_builder.add_edge(START, "echo")
    graph_builder.add_edge("echo", END)

    echo_graph = graph_builder.compile()
    echo_agent = LangGraphAgent(
        name="echo_agent",
        description="Echo agent powered by LangGraph",
        graph=echo_graph,
    )

    a2a_app = to_a2a(echo_agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_echo_app()
