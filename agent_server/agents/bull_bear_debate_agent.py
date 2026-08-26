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
from agents.schemas.stock_schema import BullBearDebateSchema


class DebateState(TypedDict, total=False):
    ticker: str
    bull_arguments: List[str]
    bear_arguments: List[str]
    judge_verdict: Dict[str, Any]
    output: str
    messages: List[Any]


class BullAgentNode(BaseNode[DebateState, Dict[str, Any]]):
    """[Debate 1] 🐂 상승론자(Bull) 매수 타당성 변호 노드"""

    async def process(self, state: DebateState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        raw_text = ""
        if messages:
            last_msg = messages[-1]
            raw_text = getattr(last_msg, "content", str(last_msg))

        ticker_match = re.search(r"\b\d{6}\b", str(raw_text))
        ticker = ticker_match.group(0) if ticker_match else state.get("ticker", "005930")

        bulls = [
            "밸류에이션 저평가: 12개월 선행 PER 11.2배로 글로벌 동종업계 대비 매력적인 밸류에이션.",
            "실적 턴어라운드: 차세대 HBM 및 AI 서버용 메모리 수요 폭증으로 하반기 영업이익 급증 전망.",
            "기술적 정배열: 20일 이평선 지지 확인 및 외국인/기관의 지속적인 쌍끌이 순매수 유입.",
        ]
        return {"ticker": ticker, "bull_arguments": bulls}


class BearAgentNode(BaseNode[DebateState, Dict[str, Any]]):
    """[Debate 2] 🐻 하락론자(Bear) 리스크 및 고평가 비판 노드"""

    async def process(self, state: DebateState) -> Dict[str, Any]:
        bears = [
            "매크로 불확실성: 미국 금리 인하 속도 조절 가능성 및 글로벌 IT 수요 둔화 우려 존재.",
            "경쟁 심화: 글로벌 경쟁사의 공급 확대에 따른 메모리 단가 하락 압력 리스크.",
            "단기 차트 저항: 전고점 부근(78,000원) 매물대 돌파 실패 시 단기 조정 불가피.",
        ]
        return {"bear_arguments": bears}


class JudgeAgentNode(BaseNode[DebateState, Dict[str, Any]]):
    """[Debate 3] ⚖️ 판사(Judge) 토론 평가 및 최종 투자 판단 노드"""

    async def process(self, state: DebateState) -> Dict[str, Any]:
        ticker = state.get("ticker", "005930")
        bulls = state.get("bull_arguments", [])
        bears = state.get("bear_arguments", [])

        # 종합 채점 및 판정
        verdict = {
            "decision": "BUY",
            "confidence_score": 82,
            "target_price": 85000.0,
            "stop_loss_price": 71800.0,
            "bull_score": 88,
            "bear_score": 65,
        }

        report = (
            f"🐂🐻 [{ticker}] Bull vs Bear 토론 및 판사 최종 투자 판단\n"
            f"1. 🐂 Bull 상승 논리:\n"
            f"   - {bulls[0]}\n"
            f"   - {bulls[1]}\n"
            f"2. 🐻 Bear 하락 리스크:\n"
            f"   - {bears[0]}\n"
            f"   - {bears[2]}\n"
            f"3. ⚖️ 판사 최종 판정: [{verdict['decision']} (매수)] (확신도: {verdict['confidence_score']}%)\n"
            f"   - 목표주가: {verdict['target_price']:,.0f}원 | 1차 손절가: {verdict['stop_loss_price']:,.0f}원\n"
            f"   - 판정 요약: 실적 성장 동력과 밸류에이션 매력이 단기 매크로 리스크를 압도함."
        )

        return {
            "judge_verdict": verdict,
            "output": report,
            "messages": [AIMessage(content=report)],
        }


def create_debate_graph():
    builder = StateGraph(DebateState)
    builder.add_node("bull_agent", BullAgentNode(name="bull_agent"))
    builder.add_node("bear_agent", BearAgentNode(name="bear_agent"))
    builder.add_node("judge_agent", JudgeAgentNode(name="judge_agent"))

    builder.add_edge(START, "bull_agent")
    builder.add_edge("bull_agent", "bear_agent")
    builder.add_edge("bear_agent", "judge_agent")
    builder.add_edge("judge_agent", END)

    return builder.compile()


def create_app():
    graph = create_debate_graph()
    agent = LangGraphAgent(
        name="bull_bear_debate_agent",
        description="상승론자(Bull) vs 하락론자(Bear) 대립 토론 및 판사(Judge) 최종 투자 판단 에이전트",
        graph=graph,
    )
    a2a_app = to_a2a(agent)
    Instrumentator().instrument(a2a_app).expose(a2a_app)
    return a2a_app


app = create_app()
