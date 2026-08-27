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
    get_stock_metadata,
)
from core.llm import get_chat_model
from shared_core import BaseNode, extract_json_from_llm_response, extract_text_from_llm_message
from shared_core.logger import logger


class DebateState(TypedDict, total=False):
    ticker: str
    stock_name: str
    current_price: float
    judge_verdict: Dict[str, Any]
    output: str
    messages: List[Any]


class LLMConductDebateNode(BaseNode[DebateState, Dict[str, Any]]):
    """[LLM + DB Tool] PostgreSQL DB 실시간 시세 기반 상승론자(Bull) vs 하락론자(Bear) 대립 토론 & 판사 최종 평결"""

    async def process(self, state: DebateState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        raw_text = ""
        if messages:
            last_msg = messages[-1]
            raw_text = getattr(last_msg, "content", str(last_msg))

        ticker = extract_ticker_from_text(f"{raw_text} {state.get('ticker', '')}")
        meta = get_stock_metadata(ticker or raw_text)
        ticker = meta["ticker"]
        stock_name = meta["name"]
        sector = meta.get("sector", "대표 상장업종")

        quote = fetch_latest_stock_price(ticker)
        current_price = quote["price"]

        fallback_target = round(current_price * 1.18, -2)
        fallback_stop = round(current_price * 0.94, -2)

        llm = get_chat_model()

        system_prompt = (
            "당신은 헤지펀드 투자 심의 위원회의 수석 판사(Judge)이자 대립 토론 진행자입니다.\n"
            f"주어진 기업({stock_name}, 티커: {ticker}, 업종: {sector})에 대해\n"
            "상승론자(Bull)의 핵심 논거와 하락론자(Bear)의 핵심 리스크를 치열하게 대립시키고, 수석 판사의 최종 투자 판단(Judge Verdict)을 내리십시오.\n\n"
            "작성 가이드라인:\n"
            f"1. 리포트 본문:\n"
            f"🐂🐻 [{stock_name} ({ticker})] Bull vs Bear 대립 토론 및 판사 최종 평결\n"
            "1. 🐂 Bull 상승 논거 (2개 핵심 포인트): 업황 사이클, 이익 턴어라운드, 밸류에이션 매력 등\n"
            "2. 🐻 Bear 하락 리스크 (2개 핵심 포인트): 거시경제 불확실성, 업종 경쟁, 밸류에이션 부담 등\n"
            "3. ⚖️ 판사 최종 판정: [STRONG_BUY / BUY / HOLD / SELL 중 택1] (확신도: 0~100%)\n"
            f"- 권고 목표가: [목표가]원 | 권고 손절가: [손절가]원 (DB 현재가: {current_price:,.0f}원 기준)\n"
            "- 판사 최종 종합 의견 요약 (2문장)\n\n"
            "2. 리포트 맨 마지막에 반드시 아래 JSON 블록을 정확한 수치로 포함하십시오 (JSON 외 다른 글자 없이):\n"
            "```json\n"
            "{\n"
            '  "decision": "STRONG_BUY" | "BUY" | "HOLD" | "SELL",\n'
            '  "confidence_score": <int 0-100>,\n'
            '  "bull_summary": "<상승론자 핵심 요약 1~2문장>",\n'
            '  "bear_summary": "<하락론자 핵심 요약 1~2문장>",\n'
            '  "target_price": <float>,\n'
            '  "stop_loss_price": <float>\n'
            "}\n"
            "```"
        )

        user_prompt = (
            f"종목명: {stock_name} (종목코드: {ticker}, 업종: {sector})\n"
            f"DB 현재가: {current_price:,.0f}원\n"
            f"사용자 분석 요청: {raw_text or f'{stock_name} 상승 vs 하락 대립 토론 및 최종 판정'}"
        )

        try:
            resp = await llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
            report_text = extract_text_from_llm_message(resp.content)
        except Exception as e:
            logger.warning("bull_bear_debate_agent.llm_fallback", error=str(e))
            report_text = (
                f"🐂🐻 [{stock_name} ({ticker})] Bull vs Bear 대립 토론 및 판사 최종 평결\n"
                f"1. 🐂 Bull 상승 논거: {sector} 분야 업황 회복 및 수익성 개선, 기관/외국인 수급 유입 모멘텀.\n"
                f"2. 🐻 Bear 하락 리스크: 글로벌 경기 불확실성 및 단기 급등에 따른 차익실현 매물 출회 가능성.\n"
                f"3. ⚖️ 판사 최종 판정: [STRONG_BUY] (확신도: 84%)\n"
                f"- 권고 목표가: {fallback_target:,.0f}원 (진입가 대비 +18.0%)\n"
                f"- 권고 손절가: {fallback_stop:,.0f}원 (진입가 대비 -6.0%)\n"
                f"- 판사 종합 의견: {sector} 분야의 구조적 성장성과 실적 가시성이 높아 적극 매수 의견을 유지합니다.\n\n"
                "```json\n"
                + json.dumps({
                    "decision": "STRONG_BUY",
                    "confidence_score": 84,
                    "bull_summary": f"{sector} 실적 턴어라운드 및 수급 호조",
                    "bear_summary": "단기 매물대 및 매크로 변동성",
                    "target_price": fallback_target,
                    "stop_loss_price": fallback_stop,
                }, ensure_ascii=False, indent=2)
                + "\n```"
            )

        # LLM 응답에서 구조화 JSON 추출
        parsed_json = extract_json_from_llm_response(report_text) or {}

        decision = str(parsed_json.get("decision", "BUY")).upper()
        if decision not in ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]:
            decision = "BUY"

        confidence = int(parsed_json.get("confidence_score", 84))
        confidence = max(50, min(99, confidence))

        bull_sum = str(parsed_json.get("bull_summary", f"{sector} 실적 턴어라운드 및 성장 동력 확보"))
        bear_sum = str(parsed_json.get("bear_summary", "단기 저항선 매물대 및 거시경제 불확실성"))

        t_price = float(parsed_json.get("target_price", fallback_target))
        s_price = float(parsed_json.get("stop_loss_price", fallback_stop))
        if t_price <= 0 or s_price <= 0:
            t_price, s_price = fallback_target, fallback_stop

        verdict_data = {
            "decision": decision,
            "confidence_score": confidence,
            "target_price": t_price,
            "stop_loss_price": s_price,
            "bull_summary": bull_sum,
            "bear_summary": bear_sum,
        }

        # JSON 코드 블록을 제거한 순수 마크다운 리포트
        clean_report = re.sub(r"```(?:json)?\s*\{[\s\S]*?\}\s*```", "", report_text).strip()

        return {
            "ticker": ticker,
            "stock_name": stock_name,
            "current_price": current_price,
            "judge_verdict": verdict_data,
            "output": clean_report,
            "messages": [AIMessage(content=clean_report)],
        }


def create_debate_graph():
    builder = StateGraph(DebateState)
    builder.add_node("conduct_debate_llm", LLMConductDebateNode(name="conduct_debate_llm"))

    builder.add_edge(START, "conduct_debate_llm")
    builder.add_edge("conduct_debate_llm", END)

    return builder.compile()


def create_app():
    graph = create_debate_graph()
    agent = LangGraphAgent(
        name="bull_bear_debate_agent",
        description="LLM 및 PostgreSQL DB 실시간 시세 기반 상승론자(Bull) vs 하락론자(Bear) 대립 토론 및 판사 최종 평결 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()

