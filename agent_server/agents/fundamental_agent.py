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
    get_fundamental_valuation,
    get_stock_metadata,
)
from core.llm import get_chat_model
from shared_core import BaseNode, extract_json_from_llm_response, extract_text_from_llm_message
from shared_core.logger import logger


class FundamentalState(TypedDict, total=False):
    ticker: str
    stock_name: str
    current_price: float
    financial_data: Dict[str, Any]
    valuation_metrics: Dict[str, Any]
    analysis_result: Dict[str, Any]
    output: str
    messages: List[Any]


class LLMAnalyzeFundamentalNode(BaseNode[FundamentalState, Dict[str, Any]]):
    """[LLM + DB Tool] PostgreSQL DB 실시간 시세 기반 LLM 펀더멘털 재무제표 심층 분석 및 밸류에이션 산출"""

    async def process(self, state: FundamentalState) -> Dict[str, Any]:
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
        db_fund = get_fundamental_valuation(ticker)

        llm = get_chat_model()

        system_prompt = (
            "당신은 여의도 제도권 대형 증권사 리서치센터의 수석 펀더멘털 밸류에이션 애널리스트입니다.\n"
            f"주어진 기업({stock_name}, 티커: {ticker}, 소속시장: {market}, 업종: {sector})에 대해\n"
            "실제 사업 모델, 최근 분기 실적 모멘텀, 영업이익률, 밸류에이션 멀티플(PER, PBR, ROE, 부채비율)을 전문적이고 현실적으로 심층 분석하여 리포트를 작성하십시오.\n\n"
            "작성 가이드라인:\n"
            f"1. 리포트 본문:\n"
            f"📈 [{stock_name} ({ticker})] 펀더멘털 & 밸류에이션 심층 분석 리포트\n"
            f"- 실시간 현재가: {current_price:,.0f}원 | 재무 평가 등급: [S / A / B / C 중 택1]\n"
            f"- 적정가치 목표 밴드: [하단목표가]원 ~ [상단목표가]원 (상승 여력 +XX.X%)\n"
            f"- 밸류에이션 멀티플: PER XX.X배 / PBR X.XX배 (업종 밸류에이션 대비 평가)\n"
            f"- 재무 건전성: ROE XX.X%, 부채비율 XX.X%\n"
            f"- 잉여현금흐름(FCF) 및 이익 가시성 (1~2문장)\n"
            f"- 애널리스트 총평 (2~3문장)\n\n"
            "2. 리포트 맨 마지막에 반드시 아래 JSON 블록을 정확한 수치로 포함하십시오 (JSON 외 다른 글자 없이):\n"
            "```json\n"
            "{\n"
            '  "grade": "S" | "A" | "B" | "C",\n'
            '  "per": <float>,\n'
            '  "pbr": <float>,\n'
            '  "roe": <float>,\n'
            '  "debt_ratio": <float>,\n'
            '  "target_price_low": <float>,\n'
            '  "target_price_high": <float>,\n'
            '  "upside_rate": <float>,\n'
            '  "fcf_summary": "<string>"\n'
            "}\n"
            "```"
        )

        user_prompt = (
            f"종목명: {stock_name} (종목코드: {ticker}, 소속: {market})\n"
            f"DB 현재가: {current_price:,.0f}원\n"
            f"분석 요청: {raw_text or f'{stock_name} 펀더멘털 및 재무제표 밸류에이션 분석'}"
        )

        try:
            resp = await llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
            report_text = extract_text_from_llm_message(resp.content)
        except Exception as e:
            logger.warning("fundamental_agent.llm_fallback", error=str(e))
            t_low, t_high = db_fund["target_price_range"]
            report_text = (
                f"📈 [{stock_name} ({ticker})] 펀더멘털 & 밸류에이션 심층 분석 리포트\n"
                f"- 실시간 현재가: {current_price:,.0f}원 | 재무 평가 등급: [{db_fund['grade']} 등급]\n"
                f"- 적정가치 목표 밴드: {t_low:,.0f}원 ~ {t_high:,.0f}원 (상승 여력 +{db_fund['upside_rate']}%)\n"
                f"- 밸류에이션 멀티플: PER {db_fund['per']:.1f}배 / PBR {db_fund['pbr']:.2f}배\n"
                f"- 재무 건전성: ROE {db_fund['roe']:.1f}%, 부채비율 {db_fund['debt_ratio']:.1f}%\n"
                f"- 애널리스트 총평: {sector} 분야 내 안정적인 영업 현금흐름과 성장성을 확보하고 있습니다.\n\n"
                "```json\n"
                + json.dumps({
                    "grade": db_fund["grade"],
                    "per": db_fund["per"],
                    "pbr": db_fund["pbr"],
                    "roe": db_fund["roe"],
                    "debt_ratio": db_fund["debt_ratio"],
                    "target_price_low": t_low,
                    "target_price_high": t_high,
                    "upside_rate": db_fund["upside_rate"],
                    "fcf_summary": f"{db_fund['fcf']:,}원",
                }, ensure_ascii=False, indent=2)
                + "\n```"
            )

        # LLM 응답에서 구조화 JSON 추출
        parsed_json = extract_json_from_llm_response(report_text) or {}
        
        per_val = float(parsed_json.get("per", db_fund["per"]))
        pbr_val = float(parsed_json.get("pbr", db_fund["pbr"]))
        roe_val = float(parsed_json.get("roe", db_fund["roe"]))
        grade_val = str(parsed_json.get("grade", db_fund["grade"])).upper()
        if grade_val not in ["S", "A", "B", "C", "D"]:
            grade_val = db_fund["grade"]

        t_low = float(parsed_json.get("target_price_low", db_fund["target_price_range"][0]))
        t_high = float(parsed_json.get("target_price_high", db_fund["target_price_range"][1]))
        if t_low <= 0 or t_high <= t_low:
            t_low, t_high = db_fund["target_price_range"]

        valuation_metrics = {
            "ticker": ticker,
            "stock_name": stock_name,
            "current_price": current_price,
            "grade": grade_val,
            "per": per_val,
            "pbr": pbr_val,
            "roe": roe_val,
            "debt_ratio": float(parsed_json.get("debt_ratio", db_fund["debt_ratio"])),
            "target_price_range": [t_low, t_high],
            "upside_rate": float(parsed_json.get("upside_rate", db_fund["upside_rate"])),
            "fcf": db_fund["fcf"],
        }

        # JSON 코드 블록을 제거한 순수 마크다운 리포트
        clean_report = re.sub(r"```(?:json)?\s*\{[\s\S]*?\}\s*```", "", report_text).strip()

        return {
            "ticker": ticker,
            "stock_name": stock_name,
            "current_price": current_price,
            "valuation_metrics": valuation_metrics,
            "output": clean_report,
            "messages": [AIMessage(content=clean_report)],
        }


def create_fundamental_graph():
    builder = StateGraph(FundamentalState)
    builder.add_node("analyze_fundamental_llm", LLMAnalyzeFundamentalNode(name="analyze_fundamental_llm"))

    builder.add_edge(START, "analyze_fundamental_llm")
    builder.add_edge("analyze_fundamental_llm", END)

    return builder.compile()


def create_app():
    graph = create_fundamental_graph()
    agent = LangGraphAgent(
        name="fundamental_agent",
        description="LLM 및 PostgreSQL DB 실데이터 기반 재무제표 밸류에이션 및 적정가치 목표 밴드 산출 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()

