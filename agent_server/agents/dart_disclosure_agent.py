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
from agents.schemas.stock_schema import DartDisclosureSchema


class DartState(TypedDict, total=False):
    ticker: str
    raw_disclosures: List[Dict[str, Any]]
    disclosure_analysis: Dict[str, Any]
    output: str
    messages: List[Any]


class FetchDartDisclosuresNode(BaseNode[DartState, Dict[str, Any]]):
    """[Rule 1] DART 전자공시 데이터 수집 및 핵심 이벤트 필터링 노드"""

    async def process(self, state: DartState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        raw_text = ""
        if messages:
            last_msg = messages[-1]
            raw_text = getattr(last_msg, "content", str(last_msg))

        ticker_match = re.search(r"\b\d{6}\b", str(raw_text))
        ticker = ticker_match.group(0) if ticker_match else state.get("ticker", "005930")

        # Mock DART Disclosures (최근 주요 공시 목록)
        disclosures = [
            {"date": "2026-08-15", "title": "단일판매·공급계약체결(자율공시)", "category": "영업활동", "impact": "POSITIVE_MODERATE"},
            {"date": "2026-08-01", "title": "분기보고서(2026.06)", "category": "정기공시", "impact": "NEUTRAL"},
            {"date": "2026-07-20", "title": "자기주식취득신탁계약체결결정", "category": "주주환원", "impact": "POSITIVE_HIGH"},
        ]

        return {"ticker": ticker, "raw_disclosures": disclosures}


class AnalyzeDisclosuresNode(BaseNode[DartState, Dict[str, Any]]):
    """[Rule 2] 공시 영향도 및 오버행/희석률 평가 노드"""

    async def process(self, state: DartState) -> Dict[str, Any]:
        disclosures = state.get("raw_disclosures", [])
        
        # 오버행 위험도 및 주주가치 영향 평가
        has_buyback = any("자기주식" in d.get("title", "") for d in disclosures)
        has_cb_bw = any("전환사채" in d.get("title", "") or "신주인수권" in d.get("title", "") for d in disclosures)

        if has_cb_bw:
            overhang_risk = "MEDIUM"
            dilution_rate = 3.5
            impact_grade = "NEGATIVE_MODERATE"
        elif has_buyback:
            overhang_risk = "LOW"
            dilution_rate = 0.0
            impact_grade = "POSITIVE_HIGH"
        else:
            overhang_risk = "NONE"
            dilution_rate = 0.0
            impact_grade = "NEUTRAL"

        analysis = {
            "overhang_risk": overhang_risk,
            "dilution_rate": dilution_rate,
            "impact_grade": impact_grade,
            "disclosure_count": len(disclosures),
        }
        return {"disclosure_analysis": analysis}


class FormatDartReportNode(BaseNode[DartState, Dict[str, Any]]):
    """[Rule 3] DART 공시 분석 리포트 생성 노드"""

    async def process(self, state: DartState) -> Dict[str, Any]:
        ticker = state.get("ticker", "005930")
        analysis = state.get("disclosure_analysis", {})
        impact = analysis.get("impact_grade", "POSITIVE_HIGH")
        overhang = analysis.get("overhang_risk", "LOW")
        count = analysis.get("disclosure_count", 3)

        report = (
            f"📑 [{ticker}] DART 전자공시 및 이벤트 분석 리포트\n"
            f"- 공시 종합 평가: [{impact}] (주주환원 및 공급계약 중심 호재성 공시)\n"
            f"- 오버행(잠재 매도물량) 리스크: [{overhang}] (CB/BW 전환 부담 없음, 자사주 매입 효과 기대)\n"
            f"- 최근 30일 공시 건수: 총 {count}건 (분기 실적보고 및 자사주 신탁 체결 포함)"
        )

        return {
            "output": report,
            "messages": [AIMessage(content=report)],
        }


def create_dart_graph():
    builder = StateGraph(DartState)
    builder.add_node("fetch_dart", FetchDartDisclosuresNode(name="fetch_dart"))
    builder.add_node("analyze_disclosures", AnalyzeDisclosuresNode(name="analyze_disclosures"))
    builder.add_node("format_report", FormatDartReportNode(name="format_report"))

    builder.add_edge(START, "fetch_dart")
    builder.add_edge("fetch_dart", "analyze_disclosures")
    builder.add_edge("analyze_disclosures", "format_report")
    builder.add_edge("format_report", END)

    return builder.compile()


def create_app():
    graph = create_dart_graph()
    agent = LangGraphAgent(
        name="dart_disclosure_agent",
        description="DART 전자공시 실시간 감지, CB/BW 희석률 및 주주환원/오버행 리스크 분석 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()
