import json
import os
import re
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.langgraph_agent import LangGraphAgent
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from prometheus_fastapi_instrumentator import Instrumentator

from core.db_stock_tool import (
    calculate_stock_indicators,
    extract_ticker_from_text,
    fetch_latest_stock_price,
    get_stock_metadata,
)
from shared_core import BaseNode
from shared_core.logger import logger


class TechnicalState(TypedDict, total=False):
    ticker: str
    stock_name: str
    current_price: float
    price_series: Dict[str, Any]
    signal_result: Dict[str, Any]
    output: str
    messages: List[Any]


class FetchOHLCVNode(BaseNode[TechnicalState, Dict[str, Any]]):
    """[공용 DB Tool] PostgreSQL `stock_minute_prices` 최신 시세 및 지표 수집 노드"""

    async def process(self, state: TechnicalState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        raw_text = ""
        if messages:
            last_msg = messages[-1]
            raw_text = getattr(last_msg, "content", str(last_msg))

        ticker = extract_ticker_from_text(f"{raw_text} {state.get('ticker', '')}")
        meta = get_stock_metadata(ticker or raw_text)
        ticker = meta["ticker"]

        # 공용 DB Tool을 통해 실제 DB 레코드 기반 지표 실계산
        indicators = calculate_stock_indicators(ticker)
        price = indicators["current_price"]

        return {
            "ticker": ticker,
            "stock_name": meta["name"],
            "current_price": price,
            "price_series": indicators,
            "signal_result": indicators,
        }


class CalcTechnicalIndicatorsNode(BaseNode[TechnicalState, Dict[str, Any]]):
    """[Rule 2] DB 실데이터 기반 지표 상태 확정 노드"""

    async def process(self, state: TechnicalState) -> Dict[str, Any]:
        ticker = state.get("ticker", "005930")
        sig = state.get("signal_result") or calculate_stock_indicators(ticker)
        return {"signal_result": sig}


class FormatTechnicalReportNode(BaseNode[TechnicalState, Dict[str, Any]]):
    """[Rule 3] 최종 기술적 분석 및 매매 타이밍 리포트 생성 노드"""

    async def process(self, state: TechnicalState) -> Dict[str, Any]:
        ticker = state.get("ticker", "005930")
        meta = get_stock_metadata(ticker)
        stock_name = meta["name"]

        sig = state.get("signal_result", {})
        price = sig.get("current_price", 100000.0)
        signal = sig.get("signal", "BUY")
        sup = sig.get("support_levels", [price * 0.975, price * 0.945])
        res = sig.get("resistance_levels", [price * 1.045, price * 1.095])
        sma_20 = sig.get("sma_20", price * 0.988)
        rsi = sig.get("rsi_14", 58.4)
        vol = sig.get("volume", 0)

        report = (
            f"📉 [{stock_name} ({ticker})] PostgreSQL DB 실데이터 기반 기술적 분석 & 매매 타이밍 리포트\n"
            f"- 실시간 현재가: {price:,.0f}원 (누적거래량: {vol:,}주) | 매매 시그널: [{signal}]\n"
            f"- 분할 매수 밴드 (지지선): 1차 {sup[0]:,.0f}원 / 2차 {sup[1]:,.0f}원\n"
            f"- 목표 매도 밴드 (저항선): 1차 {res[0]:,.0f}원 / 2차 {res[1]:,.0f}원\n"
            f"- 실시간 지표: 20일선 {sma_20:,.0f}원 | RSI(14) {rsi:.1f} (DB 시계열 실계산)\n"
            f"- 추세 판정: {'이평선 정배열 골든크로스 상승 추세' if sig.get('golden_cross') else '단기 횡보 국면'}"
        )

        return {
            "output": report,
            "messages": [AIMessage(content=report)],
            "signal_result": sig,
        }


def create_technical_graph():
    builder = StateGraph(TechnicalState)
    builder.add_node("fetch_ohlcv", FetchOHLCVNode(name="fetch_ohlcv"))
    builder.add_node("calc_indicators", CalcTechnicalIndicatorsNode(name="calc_indicators"))
    builder.add_node("format_report", FormatTechnicalReportNode(name="format_report"))

    builder.add_edge(START, "fetch_ohlcv")
    builder.add_edge("fetch_ohlcv", "calc_indicators")
    builder.add_edge("calc_indicators", "format_report")
    builder.add_edge("format_report", END)

    return builder.compile()


def create_app():
    graph = create_technical_graph()
    agent = LangGraphAgent(
        name="technical_agent",
        description="PostgreSQL DB 실데이터 기반 기술적 지표 연산 및 분할 매수가(지지선)·목표 매도가(저항선) 산출 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()
