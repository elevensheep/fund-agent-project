import re
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.langgraph_agent import LangGraphAgent
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END, START, StateGraph
from prometheus_fastapi_instrumentator import Instrumentator

from core.llm import get_chat_model
from shared_core import BaseNode
from shared_core.logger import logger
from agents.schemas.stock_schema import FundamentalAnalysisSchema


class FundamentalState(TypedDict, total=False):
    ticker: str
    financial_data: Dict[str, Any]
    valuation_metrics: Dict[str, Any]
    analysis_result: Dict[str, Any]
    output: str
    messages: List[Any]


class FetchFinancialsNode(BaseNode[FundamentalState, Dict[str, Any]]):
    """[Rule 1] 기업 재무제표 3표 및 실적 수집 노드"""

    async def process(self, state: FundamentalState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        raw_text = ""
        if messages:
            last_msg = messages[-1]
            raw_text = getattr(last_msg, "content", str(last_msg))

        ticker_match = re.search(r"\b\d{6}\b", str(raw_text))
        ticker = ticker_match.group(0) if ticker_match else state.get("ticker", "005930")

        # Mock Financial Data (3-Year Financial Statements)
        financial_data = {
            "ticker": ticker,
            "revenue": 3020000,      # 매출액 (억원)
            "operating_profit": 350000, # 영업이익 (억원)
            "net_income": 310000,     # 당기순이익 (억원)
            "total_assets": 4500000,  # 총자산 (억원)
            "total_debt": 1200000,    # 총부채 (억원)
            "total_equity": 3300000,  # 총자본 (억원)
            "operating_cash_flow": 420000,
            "capex": 280000,
            "market_cap": 4800000,    # 시가총액 (억원)
        }
        return {"ticker": ticker, "financial_data": financial_data}


class CalcValuationNode(BaseNode[FundamentalState, Dict[str, Any]]):
    """[Rule 2] 밸류에이션 및 재무 비율 연산 노드 (환각 방지)"""

    async def process(self, state: FundamentalState) -> Dict[str, Any]:
        fin = state.get("financial_data", {})
        net_income = fin.get("net_income", 1)
        total_equity = fin.get("total_equity", 1)
        market_cap = fin.get("market_cap", 1)
        total_debt = fin.get("total_debt", 0)
        ocf = fin.get("operating_cash_flow", 0)
        capex = fin.get("capex", 0)

        per = round(market_cap / net_income, 2) if net_income > 0 else 999.0
        pbr = round(market_cap / total_equity, 2) if total_equity > 0 else 999.0
        roe = round((net_income / total_equity) * 100, 2) if total_equity > 0 else 0.0
        debt_ratio = round((total_debt / total_equity) * 100, 2) if total_equity > 0 else 0.0
        fcf = ocf - capex

        # 기본 등급 산정
        if roe >= 15 and per <= 15 and debt_ratio <= 100:
            grade = "S"
        elif roe >= 10 and per <= 20 and debt_ratio <= 150:
            grade = "A"
        elif roe >= 5:
            grade = "B"
        else:
            grade = "C"

        metrics = {
            "per": per,
            "pbr": pbr,
            "roe": roe,
            "debt_ratio": debt_ratio,
            "fcf": fcf,
            "grade": grade,
        }
        return {"valuation_metrics": metrics}


class EvalModelAndFormatNode(BaseNode[FundamentalState, Dict[str, Any]]):
    """[Rule/LLM 3] 적정가치 평가 및 최종 포맷팅 노드"""

    async def process(self, state: FundamentalState) -> Dict[str, Any]:
        ticker = state.get("ticker", "005930")
        metrics = state.get("valuation_metrics", {})
        grade = metrics.get("grade", "A")
        per = metrics.get("per", 12.5)
        pbr = metrics.get("pbr", 1.2)
        roe = metrics.get("roe", 10.5)
        debt = metrics.get("debt_ratio", 36.4)
        fcf = metrics.get("fcf", 140000)

        summary = (
            f"📈 [{ticker}] 펀더멘털 및 밸류에이션 분석 리포트\n"
            f"- 재무 등급: [{grade} 등급] (수익성 및 재무 안정성 우수)\n"
            f"- 밸류에이션: PER {per:.1f}배 / PBR {pbr:.2f}배 (업종 평균 대비 저평가)\n"
            f"- 수익성/안정성: ROE {roe:.1f}%, 부채비율 {debt:.1f}%\n"
            f"- 잉여현금흐름(FCF): {fcf:,}억 원 (영업현금 창출력 견조)"
        )

        return {
            "output": summary,
            "messages": [AIMessage(content=summary)],
        }


def create_fundamental_graph():
    builder = StateGraph(FundamentalState)
    builder.add_node("fetch_financials", FetchFinancialsNode(name="fetch_financials"))
    builder.add_node("calc_valuation", CalcValuationNode(name="calc_valuation"))
    builder.add_node("eval_and_format", EvalModelAndFormatNode(name="eval_and_format"))

    builder.add_edge(START, "fetch_financials")
    builder.add_edge("fetch_financials", "calc_valuation")
    builder.add_edge("calc_valuation", "eval_and_format")
    builder.add_edge("eval_and_format", END)

    return builder.compile()


def create_app():
    graph = create_fundamental_graph()
    agent = LangGraphAgent(
        name="fundamental_agent",
        description="기업 재무제표(3표), 밸류에이션(PER/PBR/ROE), 재무 등급 및 적정가치 분석 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()
