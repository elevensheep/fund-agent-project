import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from agents.supervisor import SupervisorAgent


@pytest.mark.asyncio
async def test_supervisor_plan_and_execute():
    fake_llm = FakeMessagesListChatModel(
        responses=[AIMessage(content="[Mock] Final synthesized analysis")]
    )
    supervisor = SupervisorAgent(
        llm=fake_llm,
        remote_agents={
            "data_processing_agent": "http://localhost:28001",
            "fundamental_agent": "http://localhost:28004",
        }
    )

    res = await supervisor.ainvoke({"message": "삼성전자 005930 종합 분석해줘"})
    assert supervisor.name == "supervisor"
    assert "output" in res
    assert "used_agents" in res
    assert len(res["used_agents"]) > 0
    assert "005930" in res["output"]


@pytest.mark.asyncio
async def test_supervisor_stream():
    fake_llm = FakeMessagesListChatModel(
        responses=[AIMessage(content="Mock analysis")]
    )
    supervisor = SupervisorAgent(llm=fake_llm)
    tokens = []
    async for chunk in supervisor.astream({"message": "삼성전자 뉴스만 알려줘"}):
        tokens.append(chunk.get("token", ""))

    full_text = "".join(tokens)
    assert len(full_text) > 0
