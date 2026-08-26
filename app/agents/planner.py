import re
from pathlib import Path
from typing import List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from shared_core.logger import logger
from shared_core.prompt import load_prompt


class PlanStep(BaseModel):
    step_id: int = Field(..., description="실행 단계 번호 (동일 번호는 병렬 실행)")
    agent_name: str = Field(..., description="호출할 서브 에이전트 명 (e.g. data_processing_agent)")
    task_prompt: str = Field(..., description="서브 에이전트에 전달할 세부 지시문")


class ExecutionPlan(BaseModel):
    ticker: str = Field(default="005930", description="대상 주식 종목 코드 (6자리)")
    query_intent: str = Field(
        default="FULL_ANALYSIS",
        description="사용자 질의 의도: NEWS_ONLY, CHART_ONLY, FULL_ANALYSIS 등",
    )
    steps: List[PlanStep] = Field(
        default_factory=list,
        description="실행할 단계별 서브 에이전트 목록 (DAG)",
    )


class PlannerAgent:
    """
    사용자 질의 의도 분석 및 Plan-and-Execute 실행 계획(DAG)을 수립하는 플래너 에이전트.
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        prompt_path = Path(__file__).parent / "prompts" / "planner.yml"
        self.system_prompt = load_prompt(
            prompt_path,
            key="system_prompt",
            default="You are the Lead Investment Planner Agent. Create a structured ExecutionPlan.",
        )

    def extract_ticker(self, query: str) -> str:
        """질의에서 6자리 종목 코드 추출 (기본값: 삼성전자 005930)"""
        match = re.search(r"\b\d{6}\b", query)
        if match:
            return match.group(0)

        name_map = {
            "삼성전자": "005930",
            "sk하이닉스": "000660",
            "하이닉스": "000660",
            "네이버": "035420",
            "naver": "035420",
            "현대차": "005380",
            "카카오": "035720",
            "셀트리온": "068270",
        }
        for name, code in name_map.items():
            if name in query.lower():
                return code
        return "005930"

    def classify_intent_rule_based(self, query: str) -> str:
        """룰 기반 질의 의도 1차 분류"""
        q = query.lower()
        if any(w in q for w in ["뉴스만", "뉴스 검색", "기사만", "소식만", "news_only"]):
            return "NEWS_ONLY"
        if any(w in q for w in ["차트만", "이평선만", "기술적만", "보조지표만", "chart_only"]):
            return "CHART_ONLY"
        return "FULL_ANALYSIS"

    def build_default_plan(self, ticker: str, intent: str) -> ExecutionPlan:
        """의도에 따른 결정론적 실행 계획(DAG) 생성"""
        steps: List[PlanStep] = []

        if intent == "NEWS_ONLY":
            steps.append(
                PlanStep(
                    step_id=1,
                    agent_name="web_search_agent",
                    task_prompt=f"[{ticker}] 종목의 최신 뉴스 및 웹 정보를 검색해줘",
                )
            )
        elif intent == "CHART_ONLY":
            steps.append(
                PlanStep(
                    step_id=1,
                    agent_name="data_processing_agent",
                    task_prompt=f"[{ticker}] 종목의 시세 수집 및 지표 연산을 수행해줘",
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    agent_name="technical_agent",
                    task_prompt=f"[{ticker}] 종목의 캔들 차트, 이평선, 보조지표 및 매매신호를 분석해줘",
                )
            )
        else:  # FULL_ANALYSIS
            # Step 1: 수집 레이어 병렬 실행
            steps.append(
                PlanStep(
                    step_id=1,
                    agent_name="data_processing_agent",
                    task_prompt=f"[{ticker}] 종목 시세 수집, 뉴스 정제, 지표 가공 및 DB 적재를 수행해줘",
                )
            )
            steps.append(
                PlanStep(
                    step_id=1,
                    agent_name="web_search_agent",
                    task_prompt=f"[{ticker}] 종목의 최신 금융 뉴스 및 IR 공시를 웹에서 검색해줘",
                )
            )
            # Step 2: 심층 분석 레이어 병렬 실행
            steps.append(
                PlanStep(
                    step_id=2,
                    agent_name="fundamental_agent",
                    task_prompt=f"[{ticker}] 종목의 재무제표 3표 및 밸류에이션(PER/PBR/ROE)을 분석해줘",
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    agent_name="technical_agent",
                    task_prompt=f"[{ticker}] 종목의 기술적 지표, 지지/저항선 및 매매 시그널을 분석해줘",
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    agent_name="dart_disclosure_agent",
                    task_prompt=f"[{ticker}] 종목의 DART 전자공시 및 오버행/희석률을 분석해줘",
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    agent_name="macro_sector_agent",
                    task_prompt=f"[{ticker}] 종목의 거시경제 지표 및 섹터 로테이션 상대강도를 분석해줘",
                )
            )
            # Step 3: 토론 및 최종 판단
            steps.append(
                PlanStep(
                    step_id=3,
                    agent_name="bull_bear_debate_agent",
                    task_prompt=f"[{ticker}] 종목에 대한 Bull vs Bear 대립 토론 및 판사 최종 투자 판단을 내려줘",
                )
            )
            # Step 4: 리스크 심의 (100% Rule-Based)
            steps.append(
                PlanStep(
                    step_id=4,
                    agent_name="risk_management_agent",
                    task_prompt=f"[{ticker}] 종목에 대해 포트폴리오 비중 한도(15%), 패닉장 필터, 동적 손절선을 심의해줘",
                )
            )

        return ExecutionPlan(
            ticker=ticker,
            query_intent=intent,
            steps=steps,
        )

    async def create_plan(self, user_query: str) -> ExecutionPlan:
        """사용자 질의로부터 ExecutionPlan 수립"""
        ticker = self.extract_ticker(user_query)
        intent = self.classify_intent_rule_based(user_query)

        logger.info("planner.create_plan.start", query=user_query, ticker=ticker, intent=intent)

        try:
            if hasattr(self.llm, "with_structured_output"):
                structured_llm = self.llm.with_structured_output(ExecutionPlan)
                prompt = (
                    f"사용자 요청: '{user_query}'\n"
                    f"대상 종목 코드: {ticker}, 감지된 의도: {intent}\n"
                    f"적절한 PlanStep 목록을 구성하여 반환하세요."
                )
                res = await structured_llm.ainvoke([
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=prompt),
                ])
                if isinstance(res, ExecutionPlan) and res.steps:
                    logger.info("planner.structured_plan_generated", step_count=len(res.steps))
                    return res
        except Exception as e:
            logger.warning("planner.llm_plan_fallback", error=str(e))

        plan = self.build_default_plan(ticker, intent)
        logger.info("planner.default_plan_built", ticker=ticker, intent=intent, steps=len(plan.steps))
        return plan
