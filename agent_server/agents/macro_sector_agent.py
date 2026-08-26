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
from agents.schemas.stock_schema import MacroSectorSchema


class MacroState(TypedDict, total=False):
    ticker: str
    macro_data: Dict[str, Any]
    sector_data: Dict[str, Any]
    output: str
    messages: List[Any]


class FetchMacroDataNode(BaseNode[MacroState, Dict[str, Any]]):
    """[Rule 1] 글로벌 거시경제 지표 수집 노드"""

    async def process(self, state: MacroState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        raw_text = ""
        if messages:
            last_msg = messages[-1]
            raw_text = getattr(last_msg, "content", str(last_msg))

        ticker_match = re.search(r"\b\d{6}\b", str(raw_text))
        ticker = ticker_match.group(0) if ticker_match else state.get("ticker", "005930")

        # Mock Macro Indicators
        macro = {
            "us_fed_rate": 4.75,
            "kr_base_rate": 3.00,
            "us_10y_yield": 4.15,
            "usd_krw": 1335.0,
            "wti_oil": 74.5,
            "nasdaq_change_pct": +1.25,
            "sox_index_change_pct": +2.10,
        }
        return {"ticker": ticker, "macro_data": macro}


class AnalyzeSectorRotationNode(BaseNode[MacroState, Dict[str, Any]]):
    """[Rule 2] 섹터 로테이션 및 상대강도(RS) 산출 노드"""

    async def process(self, state: MacroState) -> Dict[str, Any]:
        macro = state.get("macro_data", {})
        sox_change = macro.get("sox_index_change_pct", 1.0)
        
        # 반도체/IT 섹터 상대강도 및 거시 점수 산출
        base_score = 70
        if sox_change > 0:
            base_score += 15
        if macro.get("usd_krw", 1300) > 1300:  # 수출주 우호 환율
            base_score += 5

        sector_info = {
            "sector_name": "반도체 및 전기전자",
            "sector_relative_strength": 1.28,
            "macro_score": min(100, base_score),
            "interest_rate_impact": "중립적 (인하 사이클 진입)",
            "exchange_rate_impact": "우호적 (고환율 수출 마진 개선)",
        }
        return {"sector_data": sector_info}


class FormatMacroReportNode(BaseNode[MacroState, Dict[str, Any]]):
    """[Rule 3] 매크로 & 섹터 종합 리포트 생성 노드"""

    async def process(self, state: MacroState) -> Dict[str, Any]:
        ticker = state.get("ticker", "005930")
        macro = state.get("macro_data", {})
        sec = state.get("sector_data", {})

        score = sec.get("macro_score", 85)
        sector_name = sec.get("sector_name", "반도체 및 전기전자")
        rs = sec.get("sector_relative_strength", 1.28)
        usd = macro.get("usd_krw", 1335.0)
        sox = macro.get("sox_index_change_pct", +2.10)

        report = (
            f"🌐 [{ticker}] 거시경제 및 섹터 트렌드 분석 리포트\n"
            f"- 매크로 종합 점수: [{score}점 / 100점] (시장 환경 우호적)\n"
            f"- 소속 섹터: [{sector_name}] (상대강도 RS: {rs:.2f} - 시장 주도 섹터)\n"
            f"- 환율/원자재: 원/달러 {usd:,.1f}원 (수출 우호) | 필라델피아 반도체 지수: {sox:+.2f}%\n"
            f"- 글로벌 증시 영향: 미국 테크주 강세 및 AI 인프라 투자 지속으로 업황 긍정적"
        )

        return {
            "output": report,
            "messages": [AIMessage(content=report)],
        }


def create_macro_graph():
    builder = StateGraph(MacroState)
    builder.add_node("fetch_macro", FetchMacroDataNode(name="fetch_macro"))
    builder.add_node("analyze_sector", AnalyzeSectorRotationNode(name="analyze_sector"))
    builder.add_node("format_report", FormatMacroReportNode(name="format_report"))

    builder.add_edge(START, "fetch_macro")
    builder.add_edge("fetch_macro", "analyze_sector")
    builder.add_edge("analyze_sector", "format_report")
    builder.add_edge("format_report", END)

    return builder.compile()


def create_app():
    graph = create_macro_graph()
    agent = LangGraphAgent(
        name="macro_sector_agent",
        description="글로벌 금리/환율/원자재 거시경제 지표 및 업종 섹터 로테이션/상대강도 분석 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()
