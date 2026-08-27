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
    get_dart_disclosure_analysis,
    get_stock_metadata,
)
from core.llm import get_chat_model
from shared_core import BaseNode, extract_json_from_llm_response, extract_text_from_llm_message
from shared_core.logger import logger


class DartState(TypedDict, total=False):
    ticker: str
    stock_name: str
    current_price: float
    raw_query: str
    disclosure_analysis: Dict[str, Any]
    output: str
    messages: List[Any]


class LLMAnalyzeDisclosureNode(BaseNode[DartState, Dict[str, Any]]):
    """[LLM + DB Tool] PostgreSQL DB 실시간 시세 및 금융감독원 DART 전자공시 & 오버행 리스크 LLM 심층 분석"""

    async def process(self, state: DartState) -> Dict[str, Any]:
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
        db_dart = get_dart_disclosure_analysis(ticker)

        llm = get_chat_model()

        system_prompt = (
            "당신은 금융감독원 DART 전자공시 및 오버행(잠재 매물) 리스크 전문 수석 분석 에이전트입니다.\n"
            f"주어진 기업({stock_name}, 티커: {ticker}, 소속: {market}, 업종: {sector})에 대해\n"
            "실제 전환사채(CB)/신주인수권부사채(BW)/유상증자 이력, 잠재 희석률, 대주주 지분 변동, 자사주 매입/소각 및 배당 등 주주환원 정책을 현실적이고 날카롭게 심의하여 리포트를 작성하십시오.\n\n"
            "작성 가이드라인:\n"
            f"1. 리포트 본문:\n"
            f"📑 [{stock_name} ({ticker})] DART 전자공시 & 오버행 리스크 분석 리포트\n"
            "- 공시 종합 평가: [POSITIVE_HIGH / POSITIVE_MODERATE / NEUTRAL / NEGATIVE_MODERATE / NEGATIVE_HIGH 중 택1]\n"
            "- 오버행 리스크: [LOW / MEDIUM / HIGH] (CB/BW 잔액 및 잠재 희석률 상태 상세)\n"
            "- 주주환원 및 지배구조: 배당 성향, 자사주 소각/매입, 책임경영 평가\n"
            "- 최근 주요 공시 3건 요약 (수주, 투자, 배당 등)\n"
            "- 핵심 요약 (2~3문장)\n\n"
            "2. 리포트 맨 마지막에 반드시 아래 JSON 블록을 정확한 수치로 포함하십시오 (JSON 외 다른 글자 없이):\n"
            "```json\n"
            "{\n"
            '  "impact_grade": "POSITIVE_HIGH" | "POSITIVE_MODERATE" | "NEUTRAL" | "NEGATIVE_MODERATE" | "NEGATIVE_HIGH",\n'
            '  "overhang_risk": "LOW" | "MEDIUM" | "HIGH",\n'
            '  "dilution_risk": "LOW" | "MEDIUM" | "HIGH",\n'
            '  "overhang_warning": true | false,\n'
            '  "cb_bw_status": "<string>",\n'
            '  "disclosure_count": <int>,\n'
            '  "latest_filings": [\n'
            '    {"title": "<공시명>", "date": "YYYY-MM-DD", "category": "<유형>", "impact": "POSITIVE" | "NEUTRAL" | "NEGATIVE"}\n'
            '  ]\n'
            "}\n"
            "```"
        )

        user_prompt = (
            f"종목명: {stock_name} (종목코드: {ticker}, 시장: {market}, 업종: {sector})\n"
            f"DB 현재가: {current_price:,.0f}원\n"
            f"사용자 분석 요청: {raw_text or f'{stock_name} 전자공시 및 오버행 리스크 분석'}"
        )

        try:
            resp = await llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
            report_text = extract_text_from_llm_message(resp.content)
        except Exception as e:
            logger.warning("dart_disclosure_agent.llm_fallback", error=str(e))
            report_text = (
                f"📑 [{stock_name} ({ticker})] DART 전자공시 & 오버행 리스크 분석 리포트\n"
                f"- 공시 종합 평가: [{db_dart['impact_grade']}] ({market} 상장사 공시 요건 충족)\n"
                f"- 오버행 리스크: [{db_dart['overhang_risk']}] ({db_dart['cb_bw_status']})\n"
                f"- 주주환원 및 지배구조: 지속적인 배당 정책 및 책임경영 추진\n"
                f"- 핵심 요약: {db_dart['summary']}\n\n"
                "```json\n"
                + json.dumps({
                    "impact_grade": db_dart["impact_grade"],
                    "overhang_risk": db_dart["overhang_risk"],
                    "dilution_risk": db_dart["dilution_risk"],
                    "overhang_warning": db_dart["overhang_warning"],
                    "cb_bw_status": db_dart["cb_bw_status"],
                    "disclosure_count": db_dart["disclosure_count"],
                    "latest_filings": db_dart.get("latest_filings", []),
                }, ensure_ascii=False, indent=2)
                + "\n```"
            )

        # LLM 응답에서 구조화 JSON 추출
        parsed_json = extract_json_from_llm_response(report_text) or {}

        impact_grade = str(parsed_json.get("impact_grade", db_dart["impact_grade"])).upper()
        if impact_grade not in ["POSITIVE_HIGH", "POSITIVE_MODERATE", "NEUTRAL", "NEGATIVE_MODERATE", "NEGATIVE_HIGH"]:
            impact_grade = db_dart["impact_grade"]

        overhang_risk = str(parsed_json.get("overhang_risk", db_dart["overhang_risk"])).upper()
        if overhang_risk not in ["LOW", "MEDIUM", "HIGH"]:
            overhang_risk = db_dart["overhang_risk"]

        dilution_risk = str(parsed_json.get("dilution_risk", overhang_risk)).upper()
        if dilution_risk not in ["LOW", "MEDIUM", "HIGH"]:
            dilution_risk = overhang_risk

        overhang_warning = bool(parsed_json.get("overhang_warning", overhang_risk != "LOW"))
        cb_bw_status = str(parsed_json.get("cb_bw_status", db_dart["cb_bw_status"]))
        count = int(parsed_json.get("disclosure_count", db_dart["disclosure_count"]))
        filings = parsed_json.get("latest_filings") or db_dart.get("latest_filings", [])

        analysis = {
            "impact_grade": impact_grade,
            "overhang_risk": overhang_risk,
            "dilution_risk": dilution_risk,
            "overhang_warning": overhang_warning,
            "cb_bw_status": cb_bw_status,
            "disclosure_count": count,
            "latest_filings": filings,
        }

        # JSON 코드 블록을 제거한 순수 마크다운 리포트
        clean_report = re.sub(r"```(?:json)?\s*\{[\s\S]*?\}\s*```", "", report_text).strip()

        return {
            "ticker": ticker,
            "stock_name": stock_name,
            "current_price": current_price,
            "disclosure_analysis": analysis,
            "output": clean_report,
            "messages": [AIMessage(content=clean_report)],
        }


def create_dart_graph():
    builder = StateGraph(DartState)
    builder.add_node("analyze_dart_llm", LLMAnalyzeDisclosureNode(name="analyze_dart_llm"))

    builder.add_edge(START, "analyze_dart_llm")
    builder.add_edge("analyze_dart_llm", END)

    return builder.compile()


def create_app():
    graph = create_dart_graph()
    agent = LangGraphAgent(
        name="dart_disclosure_agent",
        description="LLM 및 PostgreSQL DB 실시간 시세 기반 DART 전자공시 감지, CB/BW 잠재 희석률 및 오버행 리스크 분석 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()

