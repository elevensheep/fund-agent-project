# 🎨 Financial Multi-Agent Ecosystem Frontend

본 디렉토리는 **Financial Multi-Agent Ecosystem**의 차세대 웹 프론트엔드 대시보드 애플리케이션입니다.

Next.js 14+ (App Router), TypeScript, Tailwind CSS, TradingView Lightweight Charts, TanStack React Query, Zustand, React-Markdown을 기반으로 구축되었습니다.

---

## 🏛️ 주요 기능

1. **⚡ Plan-and-Execute DAG 파이프라인 시각화 (`DagTracker`)**
   - 1단계: 시세 수집 & 실시간 뉴스 정제 (`data_processing_agent`, `web_search_agent`)
   - 2단계: 4대 영역 심층 병렬 분석 (`fundamental_agent`, `technical_agent`, `dart_disclosure_agent`, `macro_sector_agent`)
   - 3단계: Bull vs Bear 대립 토론 & 판사 종합 판정 (`bull_bear_debate_agent`)
   - 4단계: 100% Rule-Based 리스크 심의 & 손절선 (`risk_management_agent`)

2. **📈 TradingView Canvas 캔들스틱 차트 (`StockChart`)**
   - 60fps 경량 캔들스틱 및 이동평균선(SMA 20, SMA 60) 토글
   - 실시간 OHLC 크로스헤어 툴팁 & 일봉/분봉/주봉 타임프레임 전환

3. **📊 8대 서브 에이전트 전문 분석 카드 위젯 (`components/insights/`)**
   - `TechnicalCard`: 골든크로스, 매매 시그널(STRONG BUY, BUY, HOLD, SELL), 지지/저항선
   - `FundamentalCard`: PER / PBR / ROE 및 재무 등급 (S~D), 적정가치 밴드
   - `DartDisclosureCard`: DART 공시 실시간 분석, 오버행(CB/BW) 및 주가 희석 경고
   - `MacroSectorCard`: 글로벌 거시경제 우호도 점수 & 섹터 상대강도(RS) 랭킹
   - `BullBearDebateCard`: 상승론 vs 하락론 대립 논거 비교 & 판사 판정
   - `RiskGatekeeperCard`: 100% Rule-Based 포트폴리오 승인 비중 (Max 15%) & ATR 동적 손절선
   - `DataProcessingCard` & `WebSearchCard`: 뉴스 센티먼트 및 웹 실시간 ReAct 검색 출처

4. **📜 제도권 리서치 보고서 뷰어 (`ReportViewer`)**
   - 마크다운 파싱 렌더링, 클립보드 원클릭 복사 및 `.md` 다운로드

5. **📊 Observability & Grafana 통합 (`GrafanaEmbed`)**
   - Prometheus 메트릭 및 Grafana 대시보드 실시간 임베딩

6. **🔄 실시간 백엔드 연동 & Standalone Mock Simulation 지원**
   - 백엔드(포트 28000) 연동 및 오프라인/테스트용 시뮬레이션 토글 제공

---

## 🚀 빠른 시작 (Local Dev)

```bash
# 1. 의존성 설치
npm install

# 2. 로컬 개발 서버 실행 (포트 3000)
npm run dev

# 3. 프로덕션 빌드
npm run build
npm start
```

---

## 🐳 Docker 컨테이너 실행

```bash
# 공유 네트워크 상에서 도커 컨테이너 빌드 & 실행
docker compose up -d --build
```
