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
from agents.schemas.stock_schema import TechnicalAnalysisSchema


class TechnicalState(TypedDict, total=False):
    ticker: str
    price_series: Dict[str, Any]
    technical_indicators: Dict[str, Any]
    signal_result: Dict[str, Any]
    output: str
    messages: List[Any]


class FetchOHLCVNode(BaseNode[TechnicalState, Dict[str, Any]]):
    """[Rule 1] 120일 시세 및 투자자 수급 데이터 수집 노드"""

    async def process(self, state: TechnicalState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        raw_text = ""
        if messages:
            last_msg = messages[-1]
            raw_text = getattr(last_msg, "content", str(last_msg))

        ticker_match = re.search(r"\b\d{6}\b", str(raw_text))
        ticker = ticker_match.group(0) if ticker_match else state.get("ticker", "005930")

        # Mock Historical Price Data (120 bars)
        base_price = 75000.0
        price_series = {
            "ticker": ticker,
            "current_price": base_price,
            "sma_20": 74200.0,
            "sma_60": 71800.0,
            "sma_120": 69500.0,
            "rsi_14": 58.4,
            "macd": 240.0,
            "macd_signal": 180.0,
            "bollinger_upper": 77500.0,
            "bollinger_lower": 71000.0,
            "atr_14": 1450.0,
            "foreign_net_5d": 1250000,   # 5일 외국인 순매수 (주)
            "inst_net_5d": 840000,       # 5일 기관 순매수 (주)
        }
        return {"ticker": ticker, "price_series": price_series}


class CalcTechnicalIndicatorsNode(BaseNode[TechnicalState, Dict[str, Any]]):
    """[Rule 2] 기술적 지표 연산 및 매매 시그널 생성 노드"""

    async def process(self, state: TechnicalState) -> Dict[str, Any]:
        p = state.get("price_series", {})
        price = p.get("current_price", 75000.0)
        sma_20 = p.get("sma_20", 74200.0)
        sma_60 = p.get("sma_60", 71800.0)
        rsi = p.get("rsi_14", 58.4)
        macd = p.get("macd", 240.0)
        macd_sig = p.get("macd_signal", 180.0)

        # 골든크로스 및 정배열 여부
        is_golden_cross = sma_20 > sma_60
        is_macd_bullish = macd > macd_sig

        # 5단계 매매 시그널 판정
        score = 0
        if price > sma_20: score += 1
        if is_golden_cross: score += 1
        if is_macd_bullish: score += 1
        if 45 <= rsi <= 65: score += 1
        if p.get("foreign_net_5d", 0) > 0: score += 1

        if score >= 4:
            signal = "STRONG_BUY"
        elif score == 3:
            signal = "BUY"
        elif score == 2:
            signal = "NEUTRAL"
        else:
            signal = "SELL"

        support_price = round(sma_60, 0)
        resistance_price = round(p.get("bollinger_upper", 78000.0), 0)

        result = {
            "signal": signal,
            "score": score,
            "support_price": support_price,
            "resistance_price": resistance_price,
            "is_golden_cross": is_golden_cross,
        }
        return {"signal_result": result}


class FormatTechnicalReportNode(BaseNode[TechnicalState, Dict[str, Any]]):
    """[Rule 3] 기술적 분석 리포트 생성 및 포맷팅 노드"""

    async def process(self, state: TechnicalState) -> Dict[str, Any]:
        ticker = state.get("ticker", "005930")
        p = state.get("price_series", {})
        sig = state.get("signal_result", {})

        current_price = p.get("current_price", 75000.0)
        signal = sig.get("signal", "BUY")
        sma_20 = p.get("sma_20", 74200.0)
        rsi = p.get("rsi_14", 58.4)
        support = sig.get("support_price", 71800.0)
        resistance = sig.get("resistance_price", 77500.0)
        foreign = p.get("foreign_net_5d", 0)

        report = (
            f"📉 [{ticker}] 기술적 차트 및 수급 분석 리포트\n"
            f"- 매매 시그널: [{signal}] (이평선 정배열 및 모멘텀 양호)\n"
            f"- 현재가: {current_price:,.0f}원 (20일선: {sma_20:,.0f}원 / RSI: {rsi:.1f})\n"
            f"- 핵심 가격대: 1차 지지선 {support:,.0f}원 | 1차 저항선 {resistance:,.0f}원\n"
            f"- 최근 5일 수급: 외국인 순매수 +{foreign:,}주 (외인·기관 쌍끌이 유입)"
        )

        return {
            "output": report,
            "messages": [AIMessage(content=report)],
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
        description="차트 패턴, 이평선 정배열, 보조지표(RSI/MACD), 수급 및 매매 타이밍 시그널 분석 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()
