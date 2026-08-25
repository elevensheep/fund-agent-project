import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from agents.factory import AgentFactory
from core.config import Settings
from core.llm import LLMRegistry


@pytest.mark.asyncio
async def test_agent_factory_create_supervisor_custom_llm():
    fake_llm = FakeMessagesListChatModel(
        responses=[AIMessage(content="Custom LLM response")]
    )
    supervisor = AgentFactory.create_supervisor(
        llm=fake_llm,
        remote_agents={"test": "http://localhost:9999"},
        mcp_server_url="http://localhost:8888",
    )
    assert supervisor.name == "supervisor"
    assert supervisor.remote_agents == {"test": "http://localhost:9999"}
    assert supervisor.mcp_server_url == "http://localhost:8888"

    res = await supervisor.ainvoke({"message": "Hello"})
    assert res["output"] == "Custom LLM response"


def test_agent_factory_create_supervisor_fallback_llm():
    LLMRegistry.shutdown()
    settings = Settings(openai_api_key="", anthropic_api_key="", google_api_key="")

    supervisor = AgentFactory.create_supervisor(settings=settings)
    assert supervisor.name == "supervisor"
    assert isinstance(supervisor.llm, FakeMessagesListChatModel)
