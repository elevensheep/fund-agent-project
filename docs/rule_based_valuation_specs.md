# 📐 Rule-Based 펀더멘털 & 기술적 분석 계산 명세서 (Valuation & Technical Rules)

본 문서는 Financial Multi-Agent 시스템에서 **환각(Hallucination) 없는 결정론적(Deterministic) 주가 분석 및 매매 타이밍**을 산출하기 위한 표준 Rule-Based 계산 공식을 정의합니다.

---

## 1. 펀더멘털 & 밸류에이션 (Fundamental & Valuation Rules)

모든 가격 산출의 기준은 **실시간 현재가 ($P_0$, Real-time Current Price)**입니다.

### 1.1. 적정가치 목표 밴드 (Fair Value Target Band)
종목의 재무 건전성 및 성장성 등급(Grade)에 따라 현재가($P_0$) 대비 적정 승수를 곱하여 산출합니다:

$$\text{Target Low} = \text{Round}_{100}\left(P_0 \times (1 + \text{Upside}_{\text{low}})\right)$$
$$\text{Target High} = \text{Round}_{100}\left(P_0 \times (1 + \text{Upside}_{\text{high}})\right)$$

| 재무 등급 (Grade) | 판정 기준 (Rule) | 상승 여력 밴드 (Upside) | 적정가치 목표 밴드 산출 공식 |
| :---: | :--- | :---: | :--- |
| **S 등급** | $\text{ROE} \ge 15\% \land \text{PER} \le 15 \land \text{부채비율} \le 100\%$ | $+15\% \sim +35\%$ | $[P_0 \times 1.15, \; P_0 \times 1.35]$ |
| **A 등급** | $\text{ROE} \ge 10\% \land \text{PER} \le 20 \land \text{부채비율} \le 150\%$ | $+10\% \sim +25\%$ | $[P_0 \times 1.10, \; P_0 \times 1.25]$ |
| **B 등급** | $\text{ROE} \ge 5\% \lor \text{PER} \le 25$ | $-5\% \sim +15\%$ | $[P_0 \times 0.95, \; P_0 \times 1.15]$ |
| **C 등급** | 기타 (저수익/고부채) | $-15\% \sim +5\%$ | $[P_0 \times 0.85, \; P_0 \times 1.05]$ |

### 1.2. 주요 밸류에이션 멀티플 계산 공식
- **PER (Price to Earnings Ratio)**: $\text{PER} = \frac{\text{시가총액}}{\text{당기순이익}} = \frac{P_0}{\text{EPS}}$
- **PBR (Price to Book Ratio)**: $\text{PBR} = \frac{\text{시가총액}}{\text{총자본(순자산)}} = \frac{P_0}{\text{BPS}}$
- **ROE (Return on Equity)**: $\text{ROE} = \left(\frac{\text{당기순이익}}{\text{총자본}}\right) \times 100$
- **부채비율 (Debt to Equity)**: $\text{Debt Ratio} = \left(\frac{\text{총부채}}{\text{총자본}}\right) \times 100$
- **잉여현금흐름 (FCF)**: $\text{FCF} = \text{영업현금흐름 (OCF)} - \text{자본적지출 (CapEx)}$

---

## 2. 기술적 분석 & 매매 타이밍 (Technical Analysis & Timing Rules)

### 2.1. 핵심 지지선 및 분할 매수 밴드 (Support & Buy Bands)
- **1차 지지선 (1차 분할 매수가)**: 당일 저가 또는 단기 지지선
  $$\text{Support}_1 = \text{Round}_{100}\left(\max(\text{Low}_{\text{today}}, \; P_0 \times 0.97)\right)$$
- **2차 지지선 (2차 분할 매수가 / 추세 지지선)**: 20일 이동평균선 또는 $-6\%$ 가격
  $$\text{Support}_2 = \text{Round}_{100}\left(P_0 \times 0.94\right)$$

### 2.2. 핵심 저항선 및 목표 매도 밴드 (Resistance & Take-Profit Bands)
- **1차 저항선 (단기 목표 매도가)**: 당일 고가 돌파 수준 또는 $+6\%$ 가격
  $$\text{Resistance}_1 = \text{Round}_{100}\left(\max(\text{High}_{\text{today}}, \; P_0 \times 1.06)\right)$$
- **2차 저항선 (중기 목표 매도가 / 볼린저 상단)**: 중기 목표가 $+12\%$ 가격
  $$\text{Resistance}_2 = \text{Round}_{100}\left(P_0 \times 1.12\right)$$

### 2.3. 5단계 기술적 종합 매매 시그널 채점표 (Score 0 ~ 5)
1. **가격 위치**: $P_0 > \text{SMA}_{20}$ (+1점)
2. **이평선 배열**: $\text{SMA}_{20} > \text{SMA}_{60}$ (골든크로스 / 정배열, +1점)
3. **모멘텀**: $\text{MACD} > \text{MACD Signal}$ (+1점)
4. **과매수/과매도**: $45 \le \text{RSI}_{14} \le 65$ (안정적 상승 국면, +1점)
5. **수급**: 외국인 또는 기관 5일 순매수 유입 (+1점)

| 획득 점수 | 최종 매매 시그널 | 가이드라인 |
| :---: | :---: | :--- |
| **4 ~ 5점** | **STRONG BUY (적극 매수)** | 정배열 및 모멘텀 최상, 분할 매수 비중 최대화 |
| **3점** | **BUY (매수)** | 추세 양호, 1차 지지선 부근 분할 매수 권고 |
| **2점** | **NEUTRAL (중립/관망)** | 지지선 테스트 확인 필요, 신규 진입 유보 |
| **0 ~ 1점** | **SELL (매도/비중축소)** | 데드크로스 또는 과열 이탈, 손절/이익실현 실행 |

---

## 3. 100% Rule-Based 리스크 관리 공식 (Risk Management Rules)

### 3.1. 필수 동적 손절가 (Dynamic Stop-Loss)
- $\text{ATR}_{14}$ (14일 평균 진폭)의 1.5배 또는 현재가 대비 $-7.0\%$를 적용하여 산출:
  $$\text{Stop Loss Price} = \text{Round}_{100}\left(P_0 - \max(\text{ATR}_{14} \times 1.5, \; P_0 \times 0.07)\right)$$

### 3.2. 포트폴리오 편입 비중 한도
- **단일 종목 최대 편입 한도**: $\le 15.0\%$
- **동일 섹터 최대 편입 한도**: $\le 30.0\%$
- **시장 급락 셧다운 룰**: KOSPI $\le -3.0\%$ 급락 시 신규 매수 전면 반려 ($\text{Approved Weight} = 0\%$)
