from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class NewsSentimentAnalysis(BaseModel):
    summary: str = Field(default="주요 뉴스 요약 없음", description="주요 뉴스 3줄 요약")
    sentiment: str = Field(default="NEUTRAL", description="시장 센티먼트: POSITIVE, NEGATIVE, NEUTRAL 중 택1")
    impact_score: int = Field(default=5, description="주가 영향도 점수 (1 ~ 10)")
    key_factors: List[str] = Field(default_factory=list, description="주가 영향 핵심 요인 목록")


class FundamentalAnalysisSchema(BaseModel):
    ticker: str = Field(default="005930", description="종목 코드")
    per: float = Field(default=12.5, description="주가수익비율 (PER)")
    pbr: float = Field(default=1.2, description="주가순자산비율 (PBR)")
    roe: float = Field(default=10.5, description="자기자본이익률 (ROE, %)")
    debt_ratio: float = Field(default=35.0, description="부채비율 (%)")
    fcf: float = Field(default=15000.0, description="잉여현금흐름 (FCF, 억원)")
    grade: str = Field(default="A", description="재무 건전성 및 밸류에이션 등급 (S, A, B, C, D)")
    summary: str = Field(default="", description="펀더멘털 분석 종합 요약")


class TechnicalAnalysisSchema(BaseModel):
    ticker: str = Field(default="005930", description="종목 코드")
    close_price: float = Field(default=75000.0, description="현재 종가")
    sma_20: float = Field(default=74000.0, description="20일 단순 이동평균")
    sma_60: float = Field(default=72000.0, description="60일 단순 이동평균")
    rsi_14: float = Field(default=55.0, description="14일 상대강도지수 (RSI)")
    macd: float = Field(default=120.0, description="MACD 오실레이터")
    bollinger_upper: float = Field(default=78000.0, description="볼린저 밴드 상단")
    bollinger_lower: float = Field(default=71000.0, description="볼린저 밴드 하단")
    atr_14: float = Field(default=1500.0, description="14일 평균 진폭 (ATR)")
    signal: str = Field(default="BUY", description="기술적 매매 신호 (STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL)")
    support_price: float = Field(default=72000.0, description="주요 지지선 가격")
    resistance_price: float = Field(default=78000.0, description="주요 저항선 가격")
    summary: str = Field(default="", description="차트 및 기술적 지표 종합 요약")


class DartDisclosureSchema(BaseModel):
    ticker: str = Field(default="005930", description="종목 코드")
    recent_disclosures: List[Dict[str, Any]] = Field(default_factory=list, description="최근 주요 공시 목록")
    overhang_risk: str = Field(default="LOW", description="오버행(잠재 매도 물량) 리스크 (HIGH, MEDIUM, LOW, NONE)")
    dilution_rate: float = Field(default=0.0, description="CB/BW 전환 시 예상 주식 희석률 (%)")
    impact_grade: str = Field(default="NEUTRAL", description="공시 종합 영향도 등급 (POSITIVE_HIGH, POSITIVE_MODERATE, NEUTRAL, NEGATIVE_MODERATE, NEGATIVE_HIGH)")
    summary: str = Field(default="", description="DART 전자공시 종합 분석 요약")


class MacroSectorSchema(BaseModel):
    macro_score: int = Field(default=65, description="거시경제 및 섹터 우호도 종합 점수 (1 ~ 100)")
    market_status: str = Field(default="NEUTRAL", description="시장 국면: BULLISH, NEUTRAL, BEARISH")
    sector_name: str = Field(default="반도체 및 IT", description="소속 주요 산업 섹터명")
    sector_relative_strength: float = Field(default=1.15, description="섹터 상대 강도 지수 (RS)")
    interest_rate_impact: str = Field(default="NEUTRAL", description="금리 환경 영향도")
    exchange_rate_impact: str = Field(default="POSITIVE", description="환율 환경 영향도")
    summary: str = Field(default="", description="거시경제 및 섹터 동향 분석 요약")


class BullBearDebateSchema(BaseModel):
    ticker: str = Field(default="005930", description="종목 코드")
    bull_thesis: List[str] = Field(default_factory=list, description="상승론자(Bull) 주요 매수 논리 목록")
    bear_thesis: List[str] = Field(default_factory=list, description="하락론자(Bear) 주요 리스크 지적 목록")
    judge_verdict: str = Field(default="BUY", description="판사 최종 판정 (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)")
    confidence_score: int = Field(default=80, description="판사 판정 확신도 (1 ~ 100%)")
    target_price: float = Field(default=85000.0, description="목표 주가")
    stop_loss_price: float = Field(default=71000.0, description="권고 손절가")
    debate_summary: str = Field(default="", description="Bull vs Bear 토론 및 판사 최종 종합 의견")


class RiskManagementSchema(BaseModel):
    ticker: str = Field(default="005930", description="종목 코드")
    proposed_weight: float = Field(default=0.15, description="제안된 포트폴리오 편입 비중")
    approved_weight: float = Field(default=0.15, description="최종 승인된 포트폴리오 편입 비중")
    verdict: str = Field(default="APPROVED", description="리스크 심의 결과 (APPROVED, ADJUSTED, REJECTED)")
    stop_loss_price: float = Field(default=71800.0, description="100% Rule 기반 산정된 필수 손절가")
    panic_status: bool = Field(default=False, description="시장 패닉/급락장 발동 여부")
    rejection_reasons: List[str] = Field(default_factory=list, description="비중 축소 또는 반려 사유 목록")
    summary: str = Field(default="", description="리스크 관리 종합 심의 의견")
