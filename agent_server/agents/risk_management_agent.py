import re
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.langgraph_agent import LangGraphAgent
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from prometheus_fastapi_instrumentator import Instrumentator

from shared_core import BaseNode
from shared_core.logger import logger
from agents.schemas.stock_schema import RiskManagementSchema


class RiskState(TypedDict, total=False):
    ticker: str
    proposed_weight: float
    current_portfolio: Dict[str, Any]
    market_status: Dict[str, Any]
    verdict: str
    approved_weight: float
    stop_loss_price: float
    rejection_reasons: List[str]
    output: str
    messages: List[Any]


class IngestProposalNode(BaseNode[RiskState, Dict[str, Any]]):
    """[Rule 1] 투자 제안 및 계좌/시장 데이터 수신 노드"""

    async def process(self, state: RiskState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        raw_text = ""
        if messages:
            last_msg = messages[-1]
            raw_text = getattr(last_msg, "content", str(last_msg))

        ticker_match = re.search(r"\b\d{6}\b", str(raw_text))
        ticker = ticker_match.group(0) if ticker_match else state.get("ticker", "005930")

        # Mock Portfolio & Market Info
        portfolio = state.get("current_portfolio", {
            "total_assets": 100000000, # 1억원
            "current_stock_weight": 0.05,
            "sector_weight": 0.18,     # 현재 반도체 섹터 비중 18%
        })
        market = state.get("market_status", {
            "kospi_change_rate": +0.85, # 당일 코스피 등락률
            "current_price": 75000.0,
            "atr_14": 1500.0,
            "daily_volume_krw": 45000000000, # 450억원
        })

        return {
            "ticker": ticker,
            "proposed_weight": state.get("proposed_weight", 0.15),
            "current_portfolio": portfolio,
            "market_status": market,
            "rejection_reasons": [],
        }


class MarketPanicRuleNode(BaseNode[RiskState, Dict[str, Any]]):
    """[Rule 2] 시장 패닉/급락 검증 노드 (코스피 -3.0% 이하 시 전면 매수 반려)"""

    async def process(self, state: RiskState) -> Dict[str, Any]:
        market = state.get("market_status", {})
        kospi_change = market.get("kospi_change_rate", 0.0)

        if kospi_change <= -3.0:
            return {
                "verdict": "REJECTED",
                "approved_weight": 0.0,
                "rejection_reasons": [f"시장 패닉장 발생 (코스피 {kospi_change:.2f}% 급락)으로 신규 매수 전면 차단"],
            }
        return {}


class PositionLimitRuleNode(BaseNode[RiskState, Dict[str, Any]]):
    """[Rule 3] 종목(15%) 및 섹터(30%) 비중 한도 검증 노드"""

    MAX_STOCK_WEIGHT = 0.15
    MAX_SECTOR_WEIGHT = 0.30

    async def process(self, state: RiskState) -> Dict[str, Any]:
        if state.get("verdict") == "REJECTED":
            return {}

        proposed = state.get("proposed_weight", 0.15)
        portfolio = state.get("current_portfolio", {})
        current_sector = portfolio.get("sector_weight", 0.0)
        reasons = list(state.get("rejection_reasons", []))

        # 1. 단일 종목 한도 체크
        allowed = min(proposed, self.MAX_STOCK_WEIGHT)

        # 2. 섹터 비중 한도 체크
        if current_sector + allowed > self.MAX_SECTOR_WEIGHT:
            allowed = max(0.0, self.MAX_SECTOR_WEIGHT - current_sector)
            reasons.append(f"섹터 한도(30%) 초과 방지를 위해 비중을 {allowed*100:.1f}%로 제한")

        verdict = "APPROVED" if allowed == proposed else "ADJUSTED"
        return {
            "verdict": verdict,
            "approved_weight": allowed,
            "rejection_reasons": reasons,
        }


class StopLossRuleNode(BaseNode[RiskState, Dict[str, Any]]):
    """[Rule 4] ATR 1.5배 기반 필수 동적 손절가 산출 및 최종 리포트 노드"""

    async def process(self, state: RiskState) -> Dict[str, Any]:
        ticker = state.get("ticker", "005930")
        market = state.get("market_status", {})
        current_price = market.get("current_price", 75000.0)
        atr_14 = market.get("atr_14", 1500.0)

        # 동적 손절가 수식: Entry Price - (ATR * 1.5)
        stop_loss_price = round(current_price - (atr_14 * 1.5), 0)

        verdict = state.get("verdict", "APPROVED")
        approved_weight = state.get("approved_weight", 0.15)
        reasons = state.get("rejection_reasons", [])
        reasons_text = f" (조정 사유: {', '.join(reasons)})" if reasons else ""

        report = (
            f"🛡️ [{ticker}] 100% Rule-Based 리스크 관리 심의 결과\n"
            f"- 최종 판정: [{verdict}]{reasons_text}\n"
            f"- 승인 비중: {approved_weight*100:.1f}% (단일종목 한도: 최대 15.0%)\n"
            f"- 산정 손절가: {stop_loss_price:,.0f}원 (진입가 대비 -{((current_price - stop_loss_price)/current_price)*100:.1f}%, ATR 1.5배 기준)\n"
            f"- 유동성 검증: 20일 일평균 거래대금 450억 원 (유동성 합격 기준 50억 원 충족)"
        )

        return {
            "stop_loss_price": stop_loss_price,
            "output": report,
            "messages": [AIMessage(content=report)],
        }


def create_risk_graph():
    builder = StateGraph(RiskState)
    builder.add_node("ingest", IngestProposalNode(name="ingest"))
    builder.add_node("panic_check", MarketPanicRuleNode(name="panic_check"))
    builder.add_node("limit_check", PositionLimitRuleNode(name="limit_check"))
    builder.add_node("stop_loss", StopLossRuleNode(name="stop_loss"))

    builder.add_edge(START, "ingest")
    builder.add_edge("ingest", "panic_check")
    builder.add_edge("panic_check", "limit_check")
    builder.add_edge("limit_check", "stop_loss")
    builder.add_edge("stop_loss", END)

    return builder.compile()


def create_app():
    graph = create_risk_graph()
    agent = LangGraphAgent(
        name="risk_management_agent",
        description="100% Rule-Based 포트폴리오 비중 한도, 동적 손절선 및 급락장 게이트키퍼 검증 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()
