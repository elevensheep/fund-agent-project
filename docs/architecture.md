# 🏛️ Agent Ecosystem 시스템 아키텍처

본 문서는 Agent Ecosystem의 다중 에이전트 오케스트레이션 아키텍처, 프로토콜 통신 흐름, 도커 네트워크 구성, 데이터베이스 및 Observability 스택을 상세히 설명합니다.

---

## 1. 개요 (Overview)

본 시스템은 **Model Context Protocol (MCP) 기반 동적 탐색(Dynamic Discovery)**과 **Google ADK A2A (Agent-to-Agent) JSON-RPC 2.0 프로토콜**을 결합하여, 중앙 Supervisor 에이전트가 분산된 8대 전문 서브 에이전트(Sub-Agents)들에게 작업을 위임하고 종합 분석 및 투자 의견을 클라이언트에게 응답하는 금융 도메인 특화 마이크로서비스 아키텍처입니다.

---

## 2. 시스템 데이터 및 프로토콜 흐름도 (Mermaid Diagram)

```mermaid
graph TD
    User["👤 클라이언트 / 투자자"] -->|1. POST /api/v1/supervisor/invoke| App

    subgraph Docker Network: agent_shared_net
        subgraph Orchestrator Server
            App["🤖 agent_orchestrator_app<br/>(Supervisor Agent / Port: 28000)"]
        end

        subgraph Protocol & Discovery Server
            MCP["🔌 agent_mcp_server<br/>(FastMCP SSE / Port: 28002)"]
        end

        subgraph Remote A2A Sub-Agents (28001, 28003~28009)
            DataProc["📊 agent_data_processing_server (28001)<br/>LangGraph Hybrid Collection & Postgres"]
            WebSearch["🔍 agent_web_search_server (28003)<br/>DuckDuckGo ReAct Search"]
            Fundamental["📈 agent_fundamental_server (28004)<br/>재무제표 & 밸류에이션 분석"]
            Technical["📉 agent_technical_server (28005)<br/>차트 패턴 & 기술적 지표"]
            Dart["📑 agent_dart_disclosure_server (28006)<br/>DART 전자공시 & 이벤트 감지"]
            Macro["🌐 agent_macro_sector_server (28007)<br/>거시경제 & 섹터 트렌드"]
            BullBear["🐂🐻 agent_bull_bear_debate_server (28008)<br/>상승 vs 하락 토론 & 판사 판정"]
            Risk["🛡️ agent_risk_management_server (28009)<br/>100% Rule-Based 리스크 게이트키퍼"]
        end

        subgraph Data Persistence & Streaming
            DB[("🐘 PostgreSQL (5432)<br/>table: stock_daily_metrics, stock_minute_prices")]
            StreamWorker["⚡ agent_stream_worker<br/>한투증권 WebSocket 실시간 틱 수집 데몬 (No LLM)"]
        end

        subgraph Monitoring Stack
            Prometheus["📊 agent_prometheus (Port: 29090)"]
            Loki["📜 agent_loki (Port: 23100)"]
            Promtail["🔍 agent_promtail"]
            Grafana["📈 agent_grafana (Port: 23000)"]
        end

        %% Dynamic Discovery flow
        App -->|2. SSE Client Connection & list_agent_cards| MCP
        MCP -.->|3. Agent Card Probing /.well-known/agent-card.json| DataProc
        MCP -.->|3. Agent Card Probing| WebSearch
        MCP -.->|3. Agent Card Probing| Fundamental
        MCP -.->|3. Agent Card Probing| Technical
        MCP -.->|3. Agent Card Probing| Dart
        MCP -.->|3. Agent Card Probing| Macro
        MCP -.->|3. Agent Card Probing| BullBear
        MCP -.->|3. Agent Card Probing| Risk
        
        %% A2A Task Delegation flow (Supervisor Hub & Spoke)
        App -->|4. A2A Task Delegation: 웹 뉴스 검색| WebSearch
        App -->|4. A2A Task Delegation: 시세 수집 & 정제/적재| DataProc
        App -->|4. A2A Task Delegation: 펀더멘털 분석| Fundamental
        App -->|4. A2A Task Delegation: 차트 기술적 분석| Technical
        App -->|4. A2A Task Delegation: 전자공시 분석| Dart
        App -->|4. A2A Task Delegation: 매크로/섹터 분석| Macro
        App -->|4. A2A Task Delegation: Bull/Bear 토론| BullBear
        App -->|4. A2A Task Delegation: Rule-Based 리스크 심의| Risk
        
        %% Data Persistence & Streaming
        StreamWorker -->|1분봉 롤링 벌크 적재| DB
        DataProc -->|시세/지표 영속화 & 조회| DB
        Technical -.->|1분봉/일봉 시세 조회| DB
        Fundamental -.->|재무 지표 조회| DB

        %% Observability flow
        Prometheus -.->|Scrape /metrics| App
        Prometheus -.->|Scrape /metrics| DataProc
        Prometheus -.->|Scrape /metrics| WebSearch
        Prometheus -.->|Scrape /metrics| Risk
        Promtail -.->|Collect Container Logs| App
        Promtail -.->|Collect Container Logs| DataProc
        Promtail -.->|Collect Container Logs| StreamWorker
        Promtail -->|Push Logs| Loki
        Grafana -->|Query Metrics| Prometheus
        Grafana -->|Query Logs| Loki
    end
```

---

## 3. 핵심 아키텍처 메커니즘

### 3.1. MCP 기반 동적 에이전트 탐색 (Dynamic Discovery)
- **정적 설정 제거**: Supervisor 에이전트는 서브 에이전트들의 IP나 엔드포인트를 하드코딩하지 않습니다.
- **MCP Server 연동**: Supervisor 실행 시 `agent_mcp_server` (FastMCP SSE)에 접속하여 `list_agent_cards` 도구를 호출합니다.
- **Agent Card 수집**: 각 서브 에이전트의 `/.well-known/agent-card.json` 엔드포인트를 통해 에이전트 메타데이터를 수집하고 Supervisor의 호출 도구로 자동 등록합니다.

### 3.2. Google ADK A2A JSON-RPC 2.0 통신 프로토콜
- **표준 메시지 규격**: 에이전트 간 메시지 전달은 Google ADK A2A JSON-RPC 2.0 규격을 준수합니다.
- **Task Delegation**: Supervisor가 수신된 사용자 요청을 분석한 뒤 적절한 서브 에이전트(`data_processing_agent`, `bull_bear_debate_agent`, `risk_management_agent` 등)에게 비동기로 메시지를 위임하고 응답 이벤트를 수집합니다.

### 3.3. Multi-Provider LLM Registry & Fallback
- **지원 프러바이더**: OpenAI (`gpt-4o`), Anthropic (`claude-3-5-sonnet`), Google GenAI (`gemini-2.5-flash`).
- **Mock LLM Fallback**: `.env`에 API 키가 설정되지 않은 경우 시스템이 중단되지 않고 `FakeMessagesListChatModel` (Mock 모드)로 안전하게 fallback 작동합니다.

### 3.4. 통합 관찰 가능성 (Observability Stack)
- **Metrics**: FastAPI Prometheus Instrumentator를 통해 각 서비스의 HTTP 요청 수, 지연시간, 에러율 메트릭 수집 (`/metrics`).
- **Logs**: `shared_core.logger`를 이용한 UTF-8 지원 Structlog 구조화 로깅. `task.*` 및 `artifact.*` 컨텍스트 로그가 출력되며 Promtail을 통해 Loki에 통합 수집되어 Grafana에서 대시보드로 조회 가능합니다.

### 3.5. `shared_core.BaseNode` 기반 표준 노드 추상화 및 DI (Dependency Injection)
- **노드 표준화**: 모든 LangGraph StateGraph 노드는 `shared_core.BaseNode` 추상 클래스를 상속받아 `@abstractmethod async def process()` 형태로 구현합니다.
- **의존성 주입(DI)**: DB 세션 팩토리, LLM 모델, A2A 클라이언트 등 외부 의존성을 노드 생성 시 주입받아 격리된 테스트와 쉬운 유지보수를 보장합니다.
- **로깅 & 실행시간 자동화**: `__call__` 엔트리포인트를 통해 노드 시작(`task.<node>.started`), 완료(`task.<node>.completed`, `duration_ms`), 실패(`task.<node>.failed`) 로그가 자동으로 남겨집니다.

### 3.6. Plan-and-Execute (Planner & Parallel Dispatcher) 오케스트레이션
- **단일 ReAct의 한계 극복**: 단일 ReAct 루프의 순차 실행 지연(30초+) 및 경로 이탈을 방지하기 위해 **Plan(계획) ➡️ Execute(병렬 디스패치) ➡️ Synthesize(종합 리포트)** 파이프라인을 적용합니다.
- **병렬 디스패치(Parallel Dispatcher)**: 독립적인 서브 에이전트들(수집 2개, 심층분석 4개)을 `asyncio.gather()`로 동시 호출하여 응답 시간을 5~10초 내외로 단축합니다.
- **동적 라우팅**: 사용자 질의 의도(`NEWS_ONLY`, `CHART_ONLY`, `FULL_ANALYSIS`)에 따라 필요한 서브 에이전트만 선별 실행하여 LLM 토큰 비용을 최적화합니다.

### 3.7. 100% Non-Blocking 완전 비동기 (Full Asynchronous) 통일 원칙
- **전구간 Non-Blocking I/O**: 동기(Blocking) I/O로 인한 이벤트 루프 멈춤 현상을 원천 방지하기 위해 시스템의 모든 I/O 레이어를 비동기(`async/await`)로 통일합니다.
  1. **HTTP / JSON-RPC 통신**: `httpx.AsyncClient` 비동기 세션 및 커넥션 풀링 활용.
  2. **Database I/O**: `SQLAlchemy AsyncSession` + `asyncpg` 비동기 PostgreSQL 드라이버.
  3. **WebSocket Streaming**: `websockets` 라이브러리 기반 비동기 실시간 틱 수신 및 백그라운드 태스크.
  4. **LangGraph Pipeline**: 모든 노드를 `async def process(self, state)`로 구현하여 `ainvoke()` 및 `astream()` 비동기 스트리밍 완벽 지원.

### 3.8. 다계층 동적 티커 식별 & 자동 적재 (Multi-Tier Stock Resolution Pipeline)
- **미등록/신규 상장사 동적 대응**: 하드코딩된 사전이나 DB에 없는 KOSPI/KOSDAQ 기업 검색 시에도 기본값(삼성전자)으로 임의 대체되지 않고 정확한 상장 종목을 동적으로 식별합니다.
  1. **Tier 1 (정규식/인메모리)**: 6자리 숫자 티커 및 주요 상장사(`STOCK_MASTER`) 사전 매칭.
  2. **Tier 2 (PostgreSQL DB)**: `stock_master_info` 테이블에서 `name ILIKE`, `ticker ILIKE`, 별칭 매칭.
  3. **Tier 3 (LLM KRX 추론 & Auto-Onboarding)**: DB 미적재 종목 질의 시 LLM 기반으로 한국거래소(KRX) 상장 종목코드(티커), 공식 사명, 시장 구분(KOSPI/KOSDAQ)을 동적 추론하고 `stock_master_info`, `stock_watchlist`, Redis에 자동 등록.
  4. **Tier 4 (종목 미식별 안내)**: 상장사가 아닌 일반 질의나 오타 입력 시 삼성전자 기본값으로 대체하지 않고 정확한 재검색 가이드 제공.

---

## 4. 네트워크 및 포트 배치표

| 컨테이너 이름 | 서비스 역할 | 호스트 포트 | 컨테이너 포트 | 네트워크 |
| :--- | :--- | :--- | :--- | :--- |
| `agent_orchestrator_app` | Supervisor API Server | `28000` | `28000` | `agent_shared_net` |
| `agent_data_processing_server` | Data Processing & DB Sub-Agent | `28001` | `28001` | `agent_shared_net` |
| `agent_mcp_server` | FastMCP Discovery Server | `28002` | `28002` | `agent_shared_net` |
| `agent_web_search_server` | Web Search ReAct Sub-Agent | `28003` | `28003` | `agent_shared_net` |
| `agent_fundamental_server` | Fundamental Analysis Sub-Agent | `28004` | `28004` | `agent_shared_net` |
| `agent_technical_server` | Technical Chart Analysis Sub-Agent | `28005` | `28005` | `agent_shared_net` |
| `agent_dart_disclosure_server` | DART Disclosure Sub-Agent | `28006` | `28006` | `agent_shared_net` |
| `agent_macro_sector_server` | Macro & Sector Sub-Agent | `28007` | `28007` | `agent_shared_net` |
| `agent_bull_bear_debate_server` | Bull vs Bear Debate Sub-Agent | `28008` | `28008` | `agent_shared_net` |
| `agent_risk_management_server` | Risk Management Gatekeeper Sub-Agent (Rule-based) | `28009` | `28009` | `agent_shared_net` |
| `agent_stream_worker` | Real-time WebSocket Ingestion Daemon (No LLM) | N/A | N/A | `agent_shared_net` |
| `postgres` | PostgreSQL Database (Relational & Timeseries) | `5432` | `5432` | `agent_shared_net` |
| `agent_prometheus` | Prometheus Metrics Server | `29090` | `9090` | `agent_shared_net` |
| `agent_loki` | Loki Log Collector | `23100` | `3100` | `agent_shared_net` |
| `agent_grafana` | Grafana Visualization UI | `23000` | `3000` | `agent_shared_net` |
