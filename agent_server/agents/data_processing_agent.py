import re
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.langgraph_agent import LangGraphAgent
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END, START, StateGraph
from prometheus_fastapi_instrumentator import Instrumentator

from core.database import async_session_factory
from core.llm import get_chat_model
from shared_core import BaseNode
from shared_core.logger import logger
from agents.nodes.collectors import CollectPriceDataNode
from agents.nodes.text_refiner import RefineNewsLLMNode
from agents.nodes.indicator_calculator import CalculateIndicatorsNode
from agents.nodes.db_processor import CombineAndSavePostgresNode


class StockProcessingState(TypedDict, total=False):
    ticker: str
    raw_price_data: Dict[str, Any]
    raw_news_text: str
    technical_metrics: Dict[str, Any]
    news_analysis: Dict[str, Any]
    db_record_id: Optional[int]
    content: str
    output: str
    messages: List[Any]


class ExtractInputNode(BaseNode[StockProcessingState, Dict[str, Any]]):
    """입력 메시지에서 종목 코드 및 뉴스 텍스트 추출 노드"""

    async def process(self, state: StockProcessingState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        raw_text = ""
        if messages:
            last_msg = messages[-1]
            if isinstance(last_msg, BaseMessage):
                raw_text = str(last_msg.content)
            elif isinstance(last_msg, dict):
                raw_text = str(last_msg.get("content", last_msg))
            else:
                raw_text = str(last_msg)

        # 6자리 종목 코드 탐색
        ticker_match = re.search(r"\b\d{6}\b", raw_text)
        ticker = ticker_match.group(0) if ticker_match else state.get("ticker", "005930")
        
        return {
            "ticker": ticker,
            "raw_news_text": raw_text or state.get("raw_news_text", ""),
        }


class FormatResponseNode(BaseNode[StockProcessingState, Dict[str, Any]]):
    """최종 리포트 메시지 포맷팅 노드"""

    async def process(self, state: StockProcessingState) -> Dict[str, Any]:
        metrics = state.get("technical_metrics", {})
        analysis = state.get("news_analysis", {})
        ticker = state.get("ticker", metrics.get("ticker", "005930"))
        close_price = metrics.get("close_price", 75000.0)
        sma_20 = metrics.get("sma_20", 74500.0)
        sentiment = analysis.get("sentiment", "NEUTRAL")
        impact_score = analysis.get("impact_score", 5)
        summary = analysis.get("summary", "데이터 처리 완료")
        db_id = state.get("db_record_id", 1)

        result_text = (
            f"📊 [{ticker}] 주식 하이브리드 데이터 취합 및 정제 리포트\n"
            f"- 현재가: {close_price:,.0f}원 (20일 SMA: {sma_20:,.0f}원)\n"
            f"- 시장 센티먼트: {sentiment} (주가 영향도: {impact_score}/10)\n"
            f"- 핵심 요약: {summary}\n"
            f"- PostgreSQL 적재 레코드 ID: #{db_id}"
        )
        
        return {
            "content": result_text,
            "output": result_text,
            "messages": [AIMessage(content=result_text)],
        }


def create_data_processing_graph():
    llm = get_chat_model()
    extract_node = ExtractInputNode(name="extract_input")
    collect_price_node = CollectPriceDataNode(name="collect_price")
    refine_news_node = RefineNewsLLMNode(name="refine_news", llm=llm)
    calc_indicators_node = CalculateIndicatorsNode(name="calc_indicators")
    save_postgres_node = CombineAndSavePostgresNode(name="save_postgres", db_session_factory=async_session_factory)
    format_response_node = FormatResponseNode(name="format_response")

    builder = StateGraph(StockProcessingState)
    builder.add_node("extract_input", extract_node)
    builder.add_node("collect_price", collect_price_node)
    builder.add_node("refine_news", refine_news_node)
    builder.add_node("calc_indicators", calc_indicators_node)
    builder.add_node("save_postgres", save_postgres_node)
    builder.add_node("format_response", format_response_node)

    builder.add_edge(START, "extract_input")
    builder.add_edge("extract_input", "collect_price")
    builder.add_edge("extract_input", "refine_news")
    builder.add_edge("collect_price", "calc_indicators")
    builder.add_edge("calc_indicators", "save_postgres")
    builder.add_edge("refine_news", "save_postgres")
    builder.add_edge("save_postgres", "format_response")
    builder.add_edge("format_response", END)

    return builder.compile()


def create_app():
    graph = create_data_processing_graph()
    agent = LangGraphAgent(
        name="data_processing_agent",
        description="LangGraph 기반 주식 데이터 하이브리드 취합(Rule/LLM) 및 PostgreSQL 연동 데이터 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()
