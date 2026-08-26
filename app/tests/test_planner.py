import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from agents.planner import PlannerAgent, ExecutionPlan, PlanStep


@pytest.mark.asyncio
async def test_planner_extract_ticker():
    fake_llm = FakeMessagesListChatModel(responses=[AIMessage(content="")])
    planner = PlannerAgent(llm=fake_llm)

    assert planner.extract_ticker("삼성전자 주가 분석해줘") == "005930"
    assert planner.extract_ticker("SK하이닉스 000660 목표가 알려줘") == "000660"
    assert planner.extract_ticker("NAVER 종합 리포트") == "035420"
    assert planner.extract_ticker("카카오 분석") == "035720"


@pytest.mark.asyncio
async def test_planner_intent_classification():
    fake_llm = FakeMessagesListChatModel(responses=[AIMessage(content="")])
    planner = PlannerAgent(llm=fake_llm)

    assert planner.classify_intent_rule_based("삼성전자 최신 뉴스 검색해줘") == "NEWS_ONLY"
    assert planner.classify_intent_rule_based("005930 차트만 분석해줘") == "CHART_ONLY"
    assert planner.classify_intent_rule_based("삼성전자 종합 분석 및 투자 심의해줘") == "FULL_ANALYSIS"


@pytest.mark.asyncio
async def test_planner_create_plan_full_analysis():
    fake_llm = FakeMessagesListChatModel(responses=[AIMessage(content="")])
    planner = PlannerAgent(llm=fake_llm)

    plan = await planner.create_plan("삼성전자(005930) 종합 분석 및 리스크 심의")
    assert isinstance(plan, ExecutionPlan)
    assert plan.ticker == "005930"
    assert plan.query_intent == "FULL_ANALYSIS"
    assert len(plan.steps) >= 8

    # Verify Step 1 contains parallel collectors
    step_1_agents = [s.agent_name for s in plan.steps if s.step_id == 1]
    assert "data_processing_agent" in step_1_agents
    assert "web_search_agent" in step_1_agents

    # Verify Step 2 contains parallel deep analyzers
    step_2_agents = [s.agent_name for s in plan.steps if s.step_id == 2]
    assert "fundamental_agent" in step_2_agents
    assert "technical_agent" in step_2_agents
    assert "dart_disclosure_agent" in step_2_agents
    assert "macro_sector_agent" in step_2_agents

    # Verify Step 3 & 4
    step_3_agents = [s.agent_name for s in plan.steps if s.step_id == 3]
    assert "bull_bear_debate_agent" in step_3_agents
    step_4_agents = [s.agent_name for s in plan.steps if s.step_id == 4]
    assert "risk_management_agent" in step_4_agents
