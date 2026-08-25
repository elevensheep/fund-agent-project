import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from agents.supervisor import SupervisorAgent


@pytest.mark.asyncio
async def test_supervisor_agent_direct_response():
    fake_llm = FakeMessagesListChatModel(
        responses=[AIMessage(content="Hello from Supervisor!")]
    )
    supervisor = SupervisorAgent(
        llm=fake_llm,
        remote_agents={"echo": "http://localhost:28001"}
    )

    res = await supervisor.ainvoke({"message": "Hi"})
    assert res["output"] == "Hello from Supervisor!"
    assert supervisor.name == "supervisor"
