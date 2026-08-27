import json
import os
import re
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.langgraph_agent import LangGraphAgent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from prometheus_fastapi_instrumentator import Instrumentator

from core.db_stock_tool import (
    extract_ticker_from_text,
    fetch_latest_stock_price,
    get_macro_sector_analysis,
    get_stock_metadata,
)
from core.llm import get_chat_model
from shared_core import BaseNode, extract_json_from_llm_response, extract_text_from_llm_message
from shared_core.logger import logger


class MacroState(TypedDict, total=False):
    ticker: str
    stock_name: str
    current_price: float
    sector_data: Dict[str, Any]
    output: str
    messages: List[Any]


class LLMAnalyzeMacroSectorNode(BaseNode[MacroState, Dict[str, Any]]):
    """[LLM + DB Tool] PostgreSQL DB 실시간 시세 및 글로벌 거시경제 & 업종 섹터 트렌드 LLM 심층 분석"""

    async def process(self, state: MacroState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        raw_text = ""
        if messages:
            last_msg = messages[-1]
            raw_text = getattr(last_msg, "content", str(last_msg))

        ticker = extract_ticker_from_text(f"{raw_text} {state.get('ticker', '')}")
        meta = get_stock_metadata(ticker or raw_text)
        ticker = meta["ticker"]
        stock_name = meta["name"]
        market = meta.get("market", "KOSPI")
        sector = meta.get("sector", "대표 우량기업")

        quote = fetch_latest_stock_price(ticker)
        current_price = quote["price"]

        # 공용 DB Tool에서 기초 참조치 산출 (LLM 폴백용 및 가이드)
        db_macro = get_macro_sector_analysis(ticker)

        llm = get_chat_model()

        system_prompt = (
            "당신은 글로벌 매크로 경제 및 산업 섹터 로테이션 전문 수석 스트래티지스트 에이전트입니다.\n"
            f"주어진 종목({stock_name}, 티커: {ticker}, 소속시장: {market}, 업종: {sector})에 대해\n"
            "글로벌 통화 정책(미 연준/한은 금리 인하 사이클), 환율(원/달러), 원자재/유가, 대미/대중 수출 환경, 소속 업종의 상대강도(RS)와 모멘텀을 전문적으로 분석하여 리포트를 작성하십시오.\n\n"
            "작성 가이드라인:\n"
            f"1. 리포트 본문:\n"
            f"🌐 [{stock_name} ({ticker})] 거시경제 및 섹터 트렌드 분석 리포트\n"
            "- 매크로 종합 점수: [0~100점 중 택1] (시장 환경 평가: 우호적 / 중립 / 비우호적)\n"
            "- 소속 섹터: [업종명] (섹터 상대강도 RS: X.XX - 시장 주도 섹터 / 시장 상회 / 시장 중립)\n"
            "- 환율/금리 영향: 환율 변동 영향 및 글로벌 금리 환경 수혜도 상세\n"
            "- 글로벌 업황 및 최종 전망 (2~3문장)\n\n"
            "2. 리포트 맨 마지막에 반드시 아래 JSON 블록을 정확한 수치로 포함하십시오 (JSON 외 다른 글자 없이):\n"
            "```json\n"
            "{\n"
            '  "sector_name": "<string>",\n'
            '  "macro_score": <int 0-100>,\n'
            '  "sector_relative_strength": <float 0.80-1.60>,\n'
            '  "relative_strength_rank": <int 1-5>,\n'
            '  "sector_momentum": "STRONG_BULL" | "BULL" | "NEUTRAL" | "BEAR",\n'
            '  "rs_description": "<string>",\n'
            '  "fx_impact": "<string>",\n'
            '  "rate_impact": "<string>",\n'
            '  "outlook": "<string>"\n'
            "}\n"
            "```"
        )

        user_prompt = (
            f"종목명: {stock_name} (종목코드: {ticker}, 업종: {sector}, 시장: {market})\n"
            f"DB 현재가: {current_price:,.0f}원\n"
            f"사용자 분석 요청: {raw_text or f'{stock_name} 매크로 및 섹터 환경 분석'}"
        )

        try:
            resp = await llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
            report_text = extract_text_from_llm_message(resp.content)
        except Exception as e:
            logger.warning("macro_sector_agent.llm_fallback", error=str(e))
            report_text = (
                f"🌐 [{stock_name} ({ticker})] 거시경제 및 섹터 트렌드 분석 리포트\n"
                f"- 매크로 종합 점수: [{db_macro['macro_score']}점 / 100점] ({'시장 환경 우호적' if db_macro['macro_score'] >= 80 else '시장 중립'})\n"
                f"- 소속 섹터: [{db_macro['sector_name']}] (상대강도 RS: {db_macro['sector_relative_strength']:.2f} - {db_macro['rs_description']})\n"
                f"- 환율/금리 영향: {db_macro['fx_impact']}\n"
                f"- 글로벌 업황 전망: {db_macro['outlook']}\n\n"
                "```json\n"
                + json.dumps({
                    "sector_name": db_macro["sector_name"],
                    "macro_score": db_macro["macro_score"],
                    "sector_relative_strength": db_macro["sector_relative_strength"],
                    "relative_strength_rank": db_macro["relative_strength_rank"],
                    "sector_momentum": db_macro["sector_momentum"],
                    "rs_description": db_macro["rs_description"],
                    "fx_impact": db_macro["fx_impact"],
                    "rate_impact": db_macro["rate_impact"],
                    "outlook": db_macro["outlook"],
                }, ensure_ascii=False, indent=2)
                + "\n```"
            )

        # LLM 응답에서 구조화 JSON 추출
        parsed_json = extract_json_from_llm_response(report_text) or {}

        sector_name = str(parsed_json.get("sector_name", db_macro["sector_name"]))
        macro_score = int(parsed_json.get("macro_score", db_macro["macro_score"]))
        macro_score = max(30, min(99, macro_score))

        rs_val = float(parsed_json.get("sector_relative_strength", db_macro["sector_relative_strength"]))
        rs_rank = int(parsed_json.get("relative_strength_rank", db_macro["relative_strength_rank"]))
        momentum = str(parsed_json.get("sector_momentum", db_macro["sector_momentum"])).upper()
        if momentum not in ["STRONG_BULL", "BULL", "NEUTRAL", "BEAR", "LEADING"]:
            momentum = db_macro["sector_momentum"]

        rs_desc = str(parsed_json.get("rs_description", db_macro["rs_description"]))
        fx_impact = str(parsed_json.get("fx_impact", db_macro["fx_impact"]))
        rate_impact = str(parsed_json.get("rate_impact", db_macro["rate_impact"]))
        outlook = str(parsed_json.get("outlook", db_macro["outlook"]))

        sector_data = {
            "ticker": ticker,
            "stock_name": stock_name,
            "sector_name": sector_name,
            "raw_sector": db_macro.get("raw_sector", sector),
            "market": market,
            "macro_score": macro_score,
            "sector_relative_strength": rs_val,
            "relative_strength_rank": rs_rank,
            "sector_momentum": momentum,
            "rs_description": rs_desc,
            "fx_impact": fx_impact,
            "rate_impact": rate_impact,
            "outlook": outlook,
        }

        # JSON 코드 블록을 제거한 순수 마크다운 리포트
        clean_report = re.sub(r"```(?:json)?\s*\{[\s\S]*?\}\s*```", "", report_text).strip()

        return {
            "ticker": ticker,
            "stock_name": stock_name,
            "current_price": current_price,
            "sector_data": sector_data,
            "output": clean_report,
            "messages": [AIMessage(content=clean_report)],
        }


def create_macro_graph():
    builder = StateGraph(MacroState)
    builder.add_node("analyze_macro_llm", LLMAnalyzeMacroSectorNode(name="analyze_macro_llm"))

    builder.add_edge(START, "analyze_macro_llm")
    builder.add_edge("analyze_macro_llm", END)

    return builder.compile()


def create_app():
    graph = create_macro_graph()
    agent = LangGraphAgent(
        name="macro_sector_agent",
        description="LLM 및 PostgreSQL DB 실시간 시세 기반 글로벌 거시경제 지표 및 산업 섹터 로테이션 분석 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()

