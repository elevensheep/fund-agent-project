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
    calculate_stock_indicators,
    extract_ticker_from_text,
    fetch_latest_stock_price,
    get_stock_metadata,
)
from core.llm import get_chat_model
from shared_core import BaseNode, extract_json_from_llm_response, extract_text_from_llm_message
from shared_core.logger import logger


class RiskState(TypedDict, total=False):
    ticker: str
    stock_name: str
    current_price: float
    proposed_weight: float
    approved_weight: float
    verdict: str
    stop_loss_price: float
    panic_status: bool
    output: str
    messages: List[Any]


class LLMRiskGatekeeperNode(BaseNode[RiskState, Dict[str, Any]]):
    """[LLM + DB Tool] DB 실시간 시세 및 ATR 기반 손절가 산정 및 LLM 수석 리스크 관리관(CRO) 심의"""

    async def process(self, state: RiskState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        raw_text = ""
        if messages:
            last_msg = messages[-1]
            raw_text = getattr(last_msg, "content", str(last_msg))

        ticker = extract_ticker_from_text(f"{raw_text} {state.get('ticker', '')}")
        meta = get_stock_metadata(ticker or raw_text)
        ticker = meta["ticker"]
        stock_name = meta["name"]
        sector = meta.get("sector", "대표 우량기업")

        # 공용 DB Tool에서 최신 실데이터 및 ATR 지표 가져오기
        indicators = calculate_stock_indicators(ticker)
        current_price = indicators["current_price"]
        atr_14 = indicators["atr_14"]

        # 변동성 비율(ATR %) 기반 리스크 패리티 권장 비중 산출
        volatility_ratio = (atr_14 / current_price) if current_price > 0 else 0.025
        if volatility_ratio <= 0.022:
            base_recommended_weight = 0.14
            tier_name = "저변동성 대형 우량주 (ATR ≤ 2.2%)"
        elif volatility_ratio <= 0.035:
            base_recommended_weight = 0.10
            tier_name = "중간 변동성 일반 상장주 (2.2% < ATR ≤ 3.5%)"
        elif volatility_ratio <= 0.050:
            base_recommended_weight = 0.065
            tier_name = "고변동성 성장/테마주 (3.5% < ATR ≤ 5.0%)"
        else:
            base_recommended_weight = 0.035
            tier_name = "초고변동성 급등락주 (ATR > 5.0%)"

        fallback_stop = round(current_price - (atr_14 * 1.5), -2)
        fallback_weight = base_recommended_weight

        llm = get_chat_model()

        system_prompt = (
            "당신은 헤지펀드 투자 심의 위원회의 수석 리스크 관리관(Chief Risk Officer, CRO)입니다.\n"
            f"주어진 종목({stock_name}, 티커: {ticker}, 업종: {sector})에 대해\n"
            f"PostgreSQL DB 실데이터 현재가({current_price:,.0f}원), 14일 ATR 변동폭({atr_14:,.0f}원, 변동성 비율: {volatility_ratio*100:.1f}%)을 바탕으로\n"
            f"변동성 패리티 가이드라인({tier_name} 기준 권장 {base_recommended_weight*100:.1f}%)을 검토하여\n"
            "단일 종목 최대 한도(15.0%) 내에서 2.0% ~ 15.0% 사이의 정밀 승인 편입 비중을 차등 심의하고,\n"
            "동적 손절선(ATR 1.5x 통제) 및 패닉장 여부를 검증하여 리스크 심의 보고서를 작성하십시오.\n\n"
            "리스크 심의 가이드라인:\n"
            "- 저변동성 대형 우량주 (ATR ≤ 2.2%): 12.0% ~ 15.0% 승인 (APPROVED)\n"
            "- 중간 변동성 일반 상장주 (2.2% < ATR ≤ 3.5%): 8.0% ~ 11.5% 승인 (APPROVED / ADJUSTED)\n"
            "- 고변동성 성장/테마주 (3.5% < ATR ≤ 5.0%): 5.0% ~ 7.5% 하향 조정 승인 (ADJUSTED)\n"
            "- 초고변동성/급등락주 (ATR > 5.0%): 2.0% ~ 4.5% 제한 승인 (ADJUSTED)\n\n"
            "작성 가이드라인:\n"
            f"1. 리포트 본문:\n"
            f"🛡️ [{stock_name} ({ticker})] 수석 리스크 관리관(CRO) 심의 결과\n"
            "- 최종 판정: [APPROVED / ADJUSTED / REJECTED 중 택1]\n"
            f"- 승인 편입 비중: [승인비중]% (변동성 {volatility_ratio*100:.1f}% 및 리스크 패리티 가이드 적용)\n"
            f"- 산정 동적 손절가: [손절가]원 (현재가 {current_price:,.0f}원 대비 -X.X%, ATR 1.5x 통제)\n"
            "- 분할 매수 밴드: 1차 매수가 / 2차 매수가\n"
            "- 리스크 심의 사유 및 CRO 총평 (2문장)\n\n"
            "2. 리포트 맨 마지막에 반드시 아래 JSON 블록을 정확한 수치로 포함하십시오 (JSON 외 다른 글자 없이):\n"
            "```json\n"
            "{\n"
            '  "verdict": "APPROVED" | "ADJUSTED" | "REJECTED",\n'
            f'  "approved_weight": <float e.g. {base_recommended_weight}>,\n'
            '  "stop_loss_price": <float>,\n'
            '  "panic_market_flag": true | false,\n'
            '  "reason": "<string>"\n'
            "}\n"
            "```"
        )

        user_prompt = (
            f"종목명: {stock_name} (종목코드: {ticker}, 업종: {sector})\n"
            f"DB 현재가: {current_price:,.0f}원, 14일 ATR 변동폭: {atr_14:,.0f}원 (변동성 비율: {volatility_ratio*100:.1f}%)\n"
            f"변동성 티어: {tier_name} (기준 권장 비중: {base_recommended_weight*100:.1f}%)\n"
            f"사용자 요청: {raw_text or f'{stock_name} 리스크 심의 및 동적 비중/손절가 확정'}"
        )

        try:
            resp = await llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
            report_text = extract_text_from_llm_message(resp.content)
        except Exception as e:
            logger.warning("risk_management_agent.llm_fallback", error=str(e))
            report_text = (
                f"🛡️ [{stock_name} ({ticker})] 수석 리스크 관리관(CRO) 심의 결과\n"
                f"- 최종 판정: [{'APPROVED' if base_recommended_weight >= 0.10 else 'ADJUSTED'}] ({tier_name})\n"
                f"- 승인 편입 비중: {fallback_weight * 100:.1f}% (변동성 {volatility_ratio*100:.1f}% 반영)\n"
                f"- 산정 동적 손절가: {fallback_stop:,.0f}원 (진입가 대비 -{((current_price - fallback_stop)/current_price)*100:.1f}%, ATR 1.5배 기준)\n"
                f"- CRO 총평: 변동성 {volatility_ratio*100:.1f}% 수준에 부합하도록 포트폴리오 비중을 {fallback_weight * 100:.1f}%로 제한 심의 승인합니다.\n\n"
                "```json\n"
                + json.dumps({
                    "verdict": "APPROVED" if base_recommended_weight >= 0.10 else "ADJUSTED",
                    "approved_weight": fallback_weight,
                    "stop_loss_price": fallback_stop,
                    "panic_market_flag": False,
                    "reason": f"{tier_name} 기준 비중 {fallback_weight*100:.1f}% 산정",
                }, ensure_ascii=False, indent=2)
                + "\n```"
            )

        # LLM 응답에서 구조화 JSON 추출
        parsed_json = extract_json_from_llm_response(report_text) or {}

        verdict = str(parsed_json.get("verdict", "APPROVED")).upper()
        if verdict not in ["APPROVED", "ADJUSTED", "REJECTED"]:
            verdict = "APPROVED"

        app_weight = float(parsed_json.get("approved_weight", fallback_weight))
        app_weight = max(0.01, min(0.15, app_weight))

        stop_loss = float(parsed_json.get("stop_loss_price", fallback_stop))
        if stop_loss <= 0 or stop_loss >= current_price:
            stop_loss = fallback_stop

        panic_flag = bool(parsed_json.get("panic_market_flag", False))
        reason = str(parsed_json.get("reason", "포트폴리오 가이드라인 100% 준수"))

        # JSON 코드 블록을 제거한 순수 마크다운 리포트
        clean_report = re.sub(r"```(?:json)?\s*\{[\s\S]*?\}\s*```", "", report_text).strip()

        return {
            "ticker": ticker,
            "stock_name": stock_name,
            "current_price": current_price,
            "proposed_weight": base_recommended_weight,
            "approved_weight": app_weight,
            "verdict": verdict,
            "stop_loss_price": stop_loss,
            "panic_status": panic_flag,
            "reason": reason,
            "output": report_text,
            "messages": [AIMessage(content=report_text)],
        }


def create_risk_graph():
    builder = StateGraph(RiskState)
    builder.add_node("evaluate_risk_llm", LLMRiskGatekeeperNode(name="evaluate_risk_llm"))

    builder.add_edge(START, "evaluate_risk_llm")
    builder.add_edge("evaluate_risk_llm", END)

    return builder.compile()


def create_app():
    graph = create_risk_graph()
    agent = LangGraphAgent(
        name="risk_management_agent",
        description="LLM 및 PostgreSQL DB 실시간 시세 기반 포트폴리오 편입 비중 승인 및 필수 동적 손절선 확정 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()

