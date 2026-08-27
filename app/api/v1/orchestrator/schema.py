from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutiveMetrics(BaseModel):
    """실시간 시세 및 8대 서브에이전트 기반 핵심 투자 지표 (Rule-Based & Structured)"""
    current_price: float = Field(..., description="실시간 현재가 (원)")
    target_price_low: float = Field(..., description="적정 목표가 밴드 하단 (원)")
    target_price_high: float = Field(..., description="적정 목표가 밴드 상단 (원)")
    target_price_str: str = Field(..., description="적정 목표가 밴드 문자열")
    stop_loss_price: float = Field(..., description="필수 동적 손절선 (원)")
    stop_loss_str: str = Field(..., description="손절선 문자열")
    approved_weight: float = Field(0.15, description="승인 포트폴리오 비중")
    approved_weight_str: str = Field("15.0%", description="승인 비중 문자열")
    confidence_score: int = Field(85, description="종합 리서치 확신도 (%)")
    confidence_str: str = Field("85%", description="확신도 문자열")
    financial_grade: str = Field("A", description="재무 건전성 등급 (S/A/B/C)")
    support_levels: List[float] = Field(default_factory=list, description="1차, 2차 분할 매수가 밴드 (원)")
    resistance_levels: List[float] = Field(default_factory=list, description="1차, 2차 목표 매도가 밴드 (원)")
    investment_opinion: str = Field("BUY", description="최종 투자 의견")


class RecommendedStock(BaseModel):
    """개별 추천 종목 상세 구조체"""
    rank: int = Field(..., description="추천 순위 (1~3)")
    ticker: str = Field(..., description="6자리 종목 코드")
    name: str = Field(..., description="종목명")
    current_price: float = Field(..., description="실시간 현재가 P0 (원)")
    opinion: str = Field("STRONG_BUY", description="투자 의견")
    target_price_range: List[float] = Field(..., description="적정 목표가 밴드 [하단, 상단]")
    target_price_str: str = Field(..., description="목표가 밴드 문자열")
    upside_percent: float = Field(..., description="목표 수익률 (%)")
    buy_levels: List[float] = Field(..., description="1차, 2차 분할 매수가")
    stop_loss_price: float = Field(..., description="필수 동적 손절가")
    approved_weight: float = Field(..., description="포트폴리오 추천 편입 비중 (0.0~1.0)")
    financial_grade: str = Field("A", description="재무 건전성 등급")
    key_catalyst: str = Field(..., description="핵심 투자 모멘텀 및 추천 사유")


class PortfolioSummary(BaseModel):
    """추천 모델 포트폴리오 총괄 요약"""
    total_equity_weight: float = Field(..., description="총 주식 비중 (예: 0.35)")
    cash_reserve_weight: float = Field(..., description="현금 완충 비중 (예: 0.65)")
    expected_return: str = Field(..., description="예상 포트폴리오 기대수익률")
    risk_level: str = Field("MODERATE", description="포트폴리오 리스크 등급 (LOW, MODERATE, HIGH)")


class RecommendationResponse(BaseModel):
    """AI 종목 추천 결과 종합 응답 스키마"""
    intent: str = Field("STOCK_RECOMMENDATION", description="인텐트")
    theme: str = Field(..., description="추천 테마명")
    recommended_stocks: List[RecommendedStock] = Field(default_factory=list, description="Top Picks 추천 종목 목록")
    portfolio_summary: PortfolioSummary = Field(..., description="모델 포트폴리오 요약")
    report_markdown: str = Field(..., description="종합 마크다운 추천 보고서")


class InvokeRequest(BaseModel):
    message: str = Field(..., description="사용자 요청 메시지")
    thread_id: Optional[str] = Field(None, description="대화 세션 식별자")
    force_refresh: bool = Field(False, description="캐시 무시 및 강제 재실행 여부")


class InvokeResponse(BaseModel):
    output: str = Field(..., description="Supervisor 최종 종합 마크다운 리포트")
    used_agents: List[str] = Field(default_factory=list, description="호출된 Remote Agent 목록")
    plan: Optional[Dict[str, Any]] = Field(None, description="Plan-and-Execute DAG 실행 계획")
    step_results: Optional[Dict[str, Any]] = Field(None, description="8대 서브에이전트별 개별 구조화 분석 결과")
    executive_metrics: Optional[ExecutiveMetrics] = Field(None, description="실시간 현재가 비례 핵심 투자 지표 메트릭")
    recommendation: Optional[RecommendationResponse] = Field(None, description="종목 추천 결과 구조체")
    remote_response: Optional[str] = Field(None, description="Remote Agent raw 응답 JSON")
    is_cached: bool = Field(False, description="Redis 캐시 데이터 여부")
    cached_at: Optional[str] = Field(None, description="캐시 적재 타임스탬프 (ISO 8601)")
    ttl_remaining: Optional[int] = Field(None, description="캐시 만료 잔여 시간 (초)")
