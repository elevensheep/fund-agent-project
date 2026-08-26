import pytest
from agents.dispatcher import ParallelDispatcher
from agents.planner import PlanStep, ExecutionPlan


@pytest.mark.asyncio
async def test_dispatcher_fallback_execution():
    dispatcher = ParallelDispatcher()
    
    steps = [
        PlanStep(step_id=1, agent_name="data_processing_agent", task_prompt="시세 수집"),
        PlanStep(step_id=1, agent_name="web_search_agent", task_prompt="뉴스 검색"),
    ]
    results = await dispatcher.execute_step_parallel(steps)
    assert len(results) == 2
    assert results[0]["success"] is True
    assert "005930" in results[0]["output"]


@pytest.mark.asyncio
async def test_dispatcher_full_plan_execution():
    dispatcher = ParallelDispatcher()
    plan = ExecutionPlan(
        ticker="005930",
        query_intent="FULL_ANALYSIS",
        steps=[
            PlanStep(step_id=1, agent_name="data_processing_agent", task_prompt="수집"),
            PlanStep(step_id=2, agent_name="fundamental_agent", task_prompt="펀더멘털"),
            PlanStep(step_id=3, agent_name="bull_bear_debate_agent", task_prompt="토론"),
            PlanStep(step_id=4, agent_name="risk_management_agent", task_prompt="리스크"),
        ]
    )

    res = await dispatcher.execute_plan(plan)
    assert res["ticker"] == "005930"
    assert len(res["used_agents"]) == 4
    assert "fundamental_agent" in res["sub_agent_results"]
    assert "risk_management_agent" in res["sub_agent_results"]
