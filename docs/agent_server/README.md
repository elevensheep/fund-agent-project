# 🗣️ Remote Sub-Agents Server (`agent_server`) 문서

본 문서는 **Agent Ecosystem의 원격 서브 에이전트 서비스인 `agent_server`**의 아키텍처, 서브 에이전트 종류, **LangGraph 기반 `수집(Rule/A2A) ➡️ 정제(LLM) ➡️ 가공(Rule)` 주식 데이터 파이프라인 및 PostgreSQL DB 연동 구조**, A2A 프로토콜 및 하네스 엔지니어링 가이드를 설명합니다.

---

## 1. 개요

`agent_server` 모듈은 Supervisor 에이전트로부터 위임받은 전문 도구 및 도메인 태스크를 독립적으로 수행하는 원격 A2A(Agent-to-Agent) 서브 에이전트들의 집합입니다.

- **하이브리드 LangGraph 데이터 프로세싱 (`수집: Rule/A2A ➡️ 정제: LLM ➡️ 가공: Rule`)**:
  - **수집 (Rule & A2A)**: 금융 API(OHLCV)를 통한 정형 시세 수집과 함께, **`web_search_agent`를 A2A(Agent-to-Agent)로 호출하여 실시간 웹 뉴스/공시 텍스트를 수집**합니다.
  - **정제 (LLM)**: 수집된 원시 웹 텍스트에서 불필요한 노이즈를 제거하고, 도메인 특화 핵심 요약 및 시장 센티먼트(호재/악재)를 **Pydantic Structured Output** 규격으로 정제합니다.
  - **가공 (Rule)**: 이동평균선(SMA), RSI 등 기술적 수치 지표를 환각 없이 초고속 연산하고, 정제된 텍스트와 결합하여 **PostgreSQL DB에 영속화(Upsert)** 및 응답을 생성합니다.
- **PostgreSQL 연동**: SQLAlchemy / asyncpg 비동기 커넥션 풀을 활용하여 주식 일봉/분봉 시세, 취합된 통계 지표, 정제 로그를 안정적으로 영속화하고 캐시 및 과거 이력을 조회합니다.
- **Google ADK `to_a2a` 표준화**: `from google.adk.a2a.utils.agent_to_a2a import to_a2a`를 적용하여 각 LangGraph 에이전트를 표준 JSON-RPC 2.0 및 HTTP 프로토콜 엔드포인트로 노출합니다.

---

## 2. 서브 에이전트 개별 문서 링크 (Sub-Agents Documentation)

각 서브 에이전트의 상세 사양 및 API 명세서는 전용 디렉토리 문서에서 확인하실 수 있습니다.

### 2.1. 데이터 수집·정제 및 웹 탐색 에이전트
| 서브 에이전트 명 | 모듈 경로 | 포트 | 주요 역할 | 개별 가이드 | API 명세서 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Data Processing Agent** | `agents/data_processing_agent.py` | `28001` | **LangGraph 주식 데이터 취합 (Rule/A2A/LLM) 및 Postgres DB 연동** | [README](data_processing_agent/README.md) | [api.md](data_processing_agent/api.md) |
| **Web Search Agent** | `agents/web_search_agent.py` | `28003` | DuckDuckGo 실시간 웹 검색 및 ReAct 자율 추론 (A2A 수집 소스) | [README](web_search_agent/README.md) | [api.md](web_search_agent/api.md) |

### 2.2. 전문 주식 분석 에이전트 (Specialized Analysis Agents)
| 서브 에이전트 명 | 모듈 경로 | 포트 | 주요 역할 | 개별 가이드 | API 명세서 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fundamental Agent** | `agents/fundamental_agent.py` | `28004` | 재무제표(3표), 밸류에이션(PER/PBR/ROE), 적정가치 평가 | [README](fundamental_agent/README.md) | [api.md](fundamental_agent/api.md) |
| **Technical Agent** | `agents/technical_agent.py` | `28005` | 차트 패턴, 이평선, 보조지표(RSI/MACD), 수급 및 매매 신호 | [README](technical_agent/README.md) | [api.md](technical_agent/api.md) |
| **DART Disclosure Agent** | `agents/dart_disclosure_agent.py` | `28006` | DART 전자공시 실시간 감지, CB/BW 희석률 및 호악재 분석 | [README](dart_disclosure_agent/README.md) | [api.md](dart_disclosure_agent/api.md) |
| **Macro & Sector Agent** | `agents/macro_sector_agent.py` | `28007` | 금리, 환율, 글로벌 증시 및 산업 섹터 트렌드 분석 | [README](macro_sector_agent/README.md) | [api.md](macro_sector_agent/api.md) |

### 2.3. 판단 및 의사결정 에이전트 (Judgment & Decision Agents)
| 서브 에이전트 명 | 모듈 경로 | 포트 | 주요 역할 | 개별 가이드 | API 명세서 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Bull vs Bear Debate Agent** | `agents/bull_bear_debate_agent.py` | `28008` | 상승(Bull) vs 하락(Bear) 대립 토론 및 판사 최종 투자 판단 | [README](bull_bear_debate_agent/README.md) | [api.md](bull_bear_debate_agent/api.md) |
| **Risk Management Agent** | `agents/risk_management_agent.py` | `28009` | **[100% Rule-Based]** 비중 한도, 동적 손절선, 급락장 게이트키퍼 검증 | [README](risk_management_agent/README.md) | [api.md](risk_management_agent/api.md) |

### 2.4. 실시간 시세 수집 데몬 (Background Ingestion Worker)
| 워커 서비스 명 | 모듈 경로 | 방식 | 주요 역할 | 개별 가이드 |
| :--- | :--- | :--- | :--- | :--- |
| **Stream Worker** | `workers/stream_worker.py` | WebSocket Daemon (No LLM) | 한국투자증권 실시간 틱 수신, 1분봉 롤링 집계 및 PostgreSQL 비동기 벌크 적재 | [README](stream_worker/README.md) |

---

## 3. 디렉토리 및 파일 구조

```text
agent_server/
├── agents/                           # A2A 웹 서비스 에이전트 모듈 (HTTP / JSON-RPC)
│   ├── data_processing_agent.py      # LangGraph 주식 데이터 취합 & DB 프로세싱 에이전트 (Port: 28001)
│   ├── web_search_agent.py           # Web 검색 에이전트 (Port: 28003)
│   ├── fundamental_agent.py          # 재무제표 & 밸류에이션 분석 에이전트 (Port: 28004)
│   ├── technical_agent.py            # 기술적 차트 & 수급 분석 에이전트 (Port: 28005)
│   ├── dart_disclosure_agent.py      # DART 전자공시 이벤트 분석 에이전트 (Port: 28006)
│   ├── macro_sector_agent.py         # 거시경제 & 섹터 트렌드 에이전트 (Port: 28007)
│   ├── bull_bear_debate_agent.py     # Bull vs Bear 토론 및 최종 투자 판단 에이전트 (Port: 28008)
│   ├── risk_management_agent.py      # 리스크 관리 & 주문 심의 게이트키퍼 에이전트 (Port: 28009)
│   ├── schemas/                      # Pydantic 구조화 스키마
│   │   ├── __init__.py
│   │   └── stock_schema.py           # LLM Structured Output 및 State 스키마
│   ├── nodes/                        # LangGraph 노드 및 파이프라인 로직
│   │   ├── __init__.py
│   │   ├── collectors.py             # [Rule/A2A] 시세 API 수집 및 web_search_agent A2A 호출 노드
│   │   ├── text_refiner.py           # [LLM] 비정형 뉴스 정제 및 감성 분석 노드
│   │   ├── indicator_calculator.py   # [Rule] 기술적 수치 지표 계산 노드
│   │   └── db_processor.py           # [Rule] PostgreSQL 저장/조회 노드
│   └── prompts/                      # 에이전트 YAML 프롬프트 정의
│       ├── data_processing.yml       # 주식 데이터 분석 및 포맷팅 템플릿
│       └── web_search.yml            # Web Search System Prompt
├── workers/                          # ⚡ [신규] 백그라운드 실시간 수집 워커 (No LLM)
│   ├── __init__.py
│   ├── stream_worker.py              # 한투증권 WebSocket 수신 & 1분봉 롤링 벌크 적재 데몬
│   ├── kis_client.py                 # 한투증권 WebSocket/REST 통신 래퍼
│   └── watchlist_manager.py          # 동적 주시 종목(Watchlist 10~40개) 선별 관리자
├── core/                             # 전역 설정, DB 및 LLM 레지스트리 (전체 공유)
│   ├── config.py                     # Settings 모듈 (한투 API 키, Postgres 설정)
│   ├── database.py                   # PostgreSQL 비동기 엔진 및 세션 관리 (SQLAlchemy/asyncpg)
│   ├── models.py                     # 주식 데이터 DB 테이블 ORM 모델 (StockMinutePrice 등)
│   └── llm.py                        # LLM Registry 및 Mock LLM 래퍼
├── Dockerfile                        # 도커 이미지 빌드 정의
├── docker-compose.yml                # 서브 에이전트 & stream_worker 도커 서비스 스펙
└── pyproject.toml                    # uv 및 의존성 패키지 명세
```

---

## 4. 원격 서브 에이전트 사양 요약

### 4.1. Data Processing Sub-Agent (`agents/data_processing_agent.py`)
- **실행 포트**: `28001`
- **컨테이너 서비스 명**: `agent_data_processing_server`
- **주요 기능**:
  - **`수집(Rule/A2A) ➡️ 정제(LLM) ➡️ 가공(Rule)` 하이브리드 파이프라인**:
    1. **수집 (`Rule` & `A2A`)**: 금융 API로 정형 시세(OHLCV)를 수집하고, `web_search_agent`에 A2A 요청을 보내 실시간 웹 뉴스 원시 데이터를 수집.
    2. **정제 (`LLM`)**: 수집된 뉴스 원시 텍스트의 노이즈를 필터링하고 Pydantic 스키마(`NewsSentimentAnalysis`) 기반으로 요약/호재/악재 정제.
    3. **가공 (`Rule`)**: 기술적 수치 지표 연산(Pandas) 및 정제된 뉴스 데이터를 결합하여 PostgreSQL DB에 적재(Upsert).
  - **PostgreSQL 연동**: 비동기 DB 커넥션을 통해 과거 시세 조회 및 취합된 주식 데이터 저장.
  - **A2A JSON-RPC 2.0 인터페이스**: Google ADK `to_a2a`를 통한 표준 A2A 메시지 교환.
- **Agent Card 엔드포인트**: `GET http://agent_data_processing_server:28001/.well-known/agent-card.json`
- 📖 [상세 README](data_processing_agent/README.md) | 🔌 [API 명세](data_processing_agent/api.md)

#### LangGraph 하이브리드 StateGraph 워크플로우 다이어그램
```mermaid
graph TD
    START([START]) --> Step1A["1-A. 주식 시세 수집 (Rule)<br/>- 종목 OHLCV, 호가 API"]
    START([START]) --> Step1B["1-B. A2A 웹 검색 수집 (A2A Delegation)<br/>- web_search_agent에 최신 뉴스 검색 위임"]
    
    subgraph Step 1. 데이터 수집 (Collection)
        Step1A
        Step1B
    end

    subgraph Step 2. 데이터 정제 (Refinement)
        Step2["2. 텍스트 정제 & 센티먼트 분석 (LLM)<br/>- 뉴스 노이즈 제거<br/>- 호재/악재 분류 & Pydantic 구조화"]
    end

    subgraph Step 3. 가공 및 적재 (Processing)
        Step3A["3-A. 기술적 수치 지표 계산 (Rule)<br/>- Pandas 이동평균(SMA), 변동성 계산"]
        Step3B["3-B. 데이터 결합 및 DB 적재 (Rule)<br/>- 수치 지표 + 정제 뉴스 결합<br/>- PostgreSQL DB Upsert / 캐싱"]
    end

    Step1B --> Step2
    Step1A --> Step3A
    
    Step2 --> Step3B
    Step3A --> Step3B
    
    Step3B --> Formatter["4. 최종 응답 포맷팅 (Rule)<br/>- Supervisor/클라이언트 응답 생성"]
    Formatter --> END([END])
```

### 4.2. Web Search Sub-Agent (`agents/web_search_agent.py`)
- **실행 포트**: `28003`
- **컨테이너 서비스 명**: `agent_web_search_server`
- **주요 기능**:
  - LangGraph `create_react_agent` 기반 ReAct 자율 추론 에이전트.
  - `web_search`: DuckDuckGo 엔진 기반 실시간 웹 검색 도구 (`duckduckgo-search`).
  - `data_processing_agent`의 수집 노드로부터 A2A 검색 위임 요청을 받아 실시간 웹 검색 결과 반환.
- **Agent Card 엔드포인트**: `GET http://agent_web_search_server:28003/.well-known/agent-card.json`
- 📖 [상세 README](web_search_agent/README.md) | 🔌 [API 명세](web_search_agent/api.md)

---

## 5. LangGraph 기반 주식 데이터 프로세싱 & PostgreSQL 연동 구현

### 5.1. 상태(State) 및 Pydantic Structured Output 정의

```python
from typing import TypedDict, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.langgraph_agent import LangGraphAgent
from prometheus_fastapi_instrumentator import Instrumentator

# 1. LLM 정제 출력을 위한 Pydantic 스키마 (Structured Output)
class NewsSentimentAnalysis(BaseModel):
    summary: str = Field(description="주요 뉴스 3줄 요약")
    sentiment: str = Field(description="시장 센티먼트: POSITIVE, NEGATIVE, NEUTRAL 중 택1")
    impact_score: int = Field(description="주가 영향도 점수 (1 ~ 10)")
    key_factors: List[str] = Field(description="주가 영향 핵심 요인 목록")

# 2. LangGraph State 정의
class StockProcessingState(TypedDict):
    ticker: str
    raw_price_data: Dict[str, Any]       # [Rule] 금융 API로부터 수집된 원시 시세 데이터 (OHLCV)
    raw_news_text: str                   # [Input] Supervisor가 전달한 최신 뉴스/웹 검색 원문
    technical_metrics: Dict[str, Any]    # [Rule] 계산된 기술적 수치 지표 (SMA, 볼린저밴드 등)
    news_analysis: Dict[str, Any]        # [LLM] 정제된 감성 분석 및 요약 구조체
    db_record_id: Optional[int]
    content: str
    messages: List[Dict[str, Any]]
```

### 5.2. `shared_core.BaseNode` 기반 하이브리드 파이프라인 노드 구현

모든 LangGraph 노드는 `shared_core.BaseNode`를 상속받아 **자동 구조화 로깅(시작/종료/소요시간/에러), 실행 시간 측정 및 외부 의존성(DB, LLM) 주입**을 일원화하여 관리합니다. 서브 에이전트는 다른 서브 에이전트를 직접 호출하지 않고 순수 독립 서비스로 동작합니다.

```python
from typing import Dict, Any
from shared_core import BaseNode

# [Node 1: Rule 수집] 주식 시세 API 수집 노드 (OHLCV)
class CollectPriceDataNode(BaseNode[StockProcessingState, Dict[str, Any]]):
    async def process(self, state: StockProcessingState) -> Dict[str, Any]:
        ticker = state.get("ticker", "005930")
        # 금융 API 호출 (OHLCV)
        raw_price = {"ticker": ticker, "close": 75000, "volume": 12000000, "prices_20d": [74000, 74500, 75000]}
        return {"raw_price_data": raw_price}

# [Node 2: LLM 정제] 입력된 뉴스 텍스트 노이즈 정제 및 Structured Output 변환 노드
class RefineNewsLLMNode(BaseNode[StockProcessingState, Dict[str, Any]]):
    async def process(self, state: StockProcessingState) -> Dict[str, Any]:
        llm = self.get_dependency("llm")
        structured_llm = llm.with_structured_output(NewsSentimentAnalysis)
        
        raw_news = state.get("raw_news_text", "")
        if not raw_news:
            return {"news_analysis": {"summary": "제공된 뉴스 없음", "sentiment": "NEUTRAL", "impact_score": 5, "key_factors": []}}
            
        prompt = f"다음 주식 관련 웹/뉴스 텍스트를 정제하고 핵심 요약과 호재/악재를 분류하세요:\n\n{raw_news}"
        analysis_result: NewsSentimentAnalysis = await structured_llm.ainvoke(prompt)
        return {"news_analysis": analysis_result.model_dump()}

# [Node 3-A: Rule 가공] 기술적 수치 지표 계산 노드
class CalculateIndicatorsNode(BaseNode[StockProcessingState, Dict[str, Any]]):
    async def process(self, state: StockProcessingState) -> Dict[str, Any]:
        price_data = state["raw_price_data"]
        prices = price_data["prices_20d"]
        sma_20 = sum(prices) / len(prices)
        metrics = {
            "ticker": price_data["ticker"],
            "close_price": price_data["close"],
            "sma_20": sma_20,
            "is_bullish": price_data["close"] > sma_20
        }
        return {"technical_metrics": metrics}

# [Node 3-B: Rule 가공 & DB 적재] 데이터 결합 및 PostgreSQL 영속화 노드
class CombineAndSavePostgresNode(BaseNode[StockProcessingState, Dict[str, Any]]):
    async def process(self, state: StockProcessingState) -> Dict[str, Any]:
        session_factory = self.get_dependency("db_session_factory")
        from core.models import StockDailyMetric
        
        metrics = state["technical_metrics"]
        analysis = state["news_analysis"]
        
        async with session_factory() as session:
            record = StockDailyMetric(
                ticker=metrics["ticker"],
                close_price=metrics["close_price"],
                sma_20=metrics["sma_20"],
                sentiment=analysis["sentiment"],
                summary=analysis["summary"]
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return {"db_record_id": record.id}

# [Node 4: Rule 응답] 최종 메시지 포맷팅 노드
class FormatResponseNode(BaseNode[StockProcessingState, Dict[str, Any]]):
    async def process(self, state: StockProcessingState) -> Dict[str, Any]:
        metrics = state["technical_metrics"]
        analysis = state["news_analysis"]
        result_text = (
            f"📊 [{metrics['ticker']}] 주식 하이브리드 분석 리포트\n"
            f"- 현재가: {metrics['close_price']:,}원 (20일 이평: {metrics['sma_20']:,.0f}원)\n"
            f"- 시장 센티먼트: {analysis['sentiment']} (영향도: {analysis.get('impact_score', 0)}/10)\n"
            f"- 핵심 뉴스 요약: {analysis['summary']}\n"
            f"- DB 저장 레코드 ID: #{state.get('db_record_id')}"
        )
        return {"content": result_text}

# 3. 노드 인스턴스화 및 의존성 주입 (DI)
from core.llm import get_chat_model
from core.database import async_session_factory

collect_price_node = CollectPriceDataNode(name="collect_price")
refine_news_node = RefineNewsLLMNode(name="refine_news", llm=get_chat_model())
calc_indicators_node = CalculateIndicatorsNode(name="calc_indicators")
save_postgres_node = CombineAndSavePostgresNode(name="save_postgres", db_session_factory=async_session_factory)
format_response_node = FormatResponseNode(name="format_response")

# 4. LangGraph StateGraph 구축 및 노드 바인딩
builder = StateGraph(StockProcessingState)
builder.add_node("collect_price", collect_price_node)
builder.add_node("refine_news", refine_news_node)
builder.add_node("calc_indicators", calc_indicators_node)
builder.add_node("save_postgres", save_postgres_node)
builder.add_node("format_response", format_response_node)

# 그래프 엣지 구성
builder.add_edge(START, "collect_price")
builder.add_edge(START, "refine_news")

builder.add_edge("collect_price", "calc_indicators")

builder.add_edge("calc_indicators", "save_postgres")
builder.add_edge("refine_news", "save_postgres")

builder.add_edge("save_postgres", "format_response")
builder.add_edge("format_response", END)

stock_graph = builder.compile()

# 4. ADK LangGraphAgent 및 to_a2a 래핑
data_processing_agent = LangGraphAgent(
    name="data_processing_agent",
    description="LangGraph 기반 주식 데이터 하이브리드 취합(Rule/LLM) 및 PostgreSQL 연동 데이터 에이전트",
    graph=stock_graph,
)

a2a_app = to_a2a(data_processing_agent)
Instrumentator().instrument(a2a_app).expose(a2a_app)
app = a2a_app
```

---

## 6. 하이브리드 파이프라인 설계 원칙 및 모범 사례 (Best Practices)

| 단계 | 방식 | 처리 대상 | 핵심 역할 및 아키텍처 이점 |
| :--- | :--- | :--- | :--- |
| **1. 시세 수집** | `Rule (API)` | 시세 API (OHLCV) | • 정형 시계열 데이터 안정적 수집 및 빠른 응답 |
| **2. 텍스트 정제** | `LLM (Structured Output)` | 수집된 웹/뉴스 텍스트 | • 불필요 광고 및 노이즈 완벽 제거<br/>• **Pydantic 스키마 강제**로 일관된 정제 구조체 반환 |
| **3-A. 지표 연산** | `Rule (Pandas/Numpy)` | 시세 시계열 데이터 | • **환각(Hallucination) 원천 차단**<br/>• 마이크로초 단위의 초고속 수치 연산 |
| **3-B. 결합 & 적재** | `Rule (ORM/asyncpg)` | 지표 + 정제 분석 통합 데이터 | • PostgreSQL 비동기 트랜잭션 적재 및 캐시 갱신 |
| **4. 리스크 & 검증 (Validator)** | `Rule (100% Deterministic)` | 투자 제안, 비중 한도, 손절가 | • **환각 0% 원천 차단**: 잘못된 승인 방지<br/>• 종목(15%)/섹터(30%) 한도 초과 시 자동 수량 조정<br/>• ATR 1.5배 기반 칼 같은 손절가 계산 |
| **5. 응답 포맷팅** | `Rule (Template)` | 최종 반환 메시지 | • 결정론적이고 일관된 A2A JSON-RPC 응답 제공 |

---

## 7. PostgreSQL 연동 및 환경 변수 설정

### 7.1. 환경 변수 (`.env`)
```env
# PostgreSQL Database Settings
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=agent_stock_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_secure_pw

# Database Connection Pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### 7.2. PostgreSQL 주식 데이터 테이블 스키마 (예시)
```sql
CREATE TABLE IF NOT EXISTS stock_daily_metrics (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    close_price NUMERIC(12, 2) NOT NULL,
    sma_20 NUMERIC(12, 2),
    sentiment VARCHAR(20),
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stock_ticker_date ON stock_daily_metrics (ticker, created_at DESC);
```

---

## 8. A2A 서버 구성 및 테스트 하네스

각 서브 에이전트는 `to_a2a(agent)` 함수를 통해 Starlette/FastAPI 애플리케이션으로 포장되며, `prometheus_fastapi_instrumentator`를 통해 수집 엔드포인트를 노출합니다.

- **서버 독립 실행**:
  ```bash
  uvicorn agent_server.agents.data_processing_agent:app --host 0.0.0.0 --port 28001
  ```
- **Agent Card 하네스 테스트**:
  ```bash
  curl -s http://localhost:28001/.well-known/agent-card.json | jq .
  ```
- **A2A 주식 데이터 하이브리드 취합 작업 위임 호출**:
  ```bash
  curl -X POST http://localhost:28001/ \
    -H "Content-Type: application/json" \
    -d '{
      "jsonrpc": "2.0",
      "method": "SendMessage",
      "params": {
        "message": {
          "role": "user",
          "content": "005930 종목의 최신 시세 및 뉴스 데이터를 하이브리드 파이프라인으로 정제하고 DB에 적재해줘"
        }
      },
      "id": "req-stock-001"
    }'
  ```
- **메트릭 수집 검증**:
  ```bash
  curl -s http://localhost:28001/metrics
  ```

