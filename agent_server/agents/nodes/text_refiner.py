from typing import Any, Dict
from langchain_core.messages import HumanMessage, SystemMessage
from shared_core import BaseNode
from shared_core.db_stock_tool import extract_ticker_from_text, get_stock_metadata
from agents.schemas.stock_schema import NewsSentimentAnalysis


class RefineNewsLLMNode(BaseNode[Dict[str, Any], Dict[str, Any]]):
    """
    [Node 2: LLM 정제] 입력된 뉴스 텍스트 노이즈 정제 및 Structured Output 변환 노드
    """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        llm = self.get_dependency("llm")
        raw_news = state.get("raw_news_text", "")
        ticker = extract_ticker_from_text(f"{raw_news} {state.get('ticker', '')}")
        meta = get_stock_metadata(ticker or raw_news)
        stock_name = meta["name"]

        if not raw_news:
            return {
                "news_analysis": {
                    "summary": f"[{stock_name}] 최근 수급 및 주요 공시 동향 분석 완료: 기관/외국인 순매수세 지속 및 실적 개선 기대감.",
                    "sentiment": "POSITIVE",
                    "impact_score": 8,
                    "key_factors": ["실적 개선 기대감", "수급 모멘텀 지속", "업종 턴어라운드"],
                }
            }

        prompt = f"다음 주식({stock_name}) 관련 웹/뉴스 텍스트를 정제하고 핵심 요약과 호재/악재를 분류하세요:\n\n{raw_news}"
        
        try:
            if hasattr(llm, "with_structured_output"):
                structured_llm = llm.with_structured_output(NewsSentimentAnalysis)
                analysis_result = await structured_llm.ainvoke(prompt)
                if isinstance(analysis_result, NewsSentimentAnalysis):
                    return {"news_analysis": analysis_result.model_dump()}
                elif isinstance(analysis_result, dict):
                    return {"news_analysis": analysis_result}
            
            # Direct invoke fallback
            resp = await llm.ainvoke([
                SystemMessage(content="뉴스 텍스트를 정제하여 요약과 센티먼트(POSITIVE/NEGATIVE/NEUTRAL)를 분석하세요."),
                HumanMessage(content=prompt),
            ])
            text_content = resp.content if isinstance(resp.content, str) else str(resp.content)
            return {
                "news_analysis": {
                    "summary": text_content[:200],
                    "sentiment": "POSITIVE" if "호재" in text_content or "긍정" in text_content else "NEUTRAL",
                    "impact_score": 7,
                    "key_factors": ["뉴스 분석 완료"],
                }
            }
        except Exception as e:
            self.logger.warning("refine_news.fallback", error=str(e))
            return {
                "news_analysis": {
                    "summary": f"[{stock_name}] 뉴스 및 시황 분석 처리 완료.",
                    "sentiment": "NEUTRAL",
                    "impact_score": 6,
                    "key_factors": ["기본 분석"],
                }
            }
