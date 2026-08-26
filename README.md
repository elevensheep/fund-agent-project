# Agent Ecosystem (Financial Multi-Agent Orchestrator)

다중 에이전트 오케스트레이션 시스템으로, **Model Context Protocol (MCP) 기반 동적 탐색(Dynamic Discovery)**, **Google ADK A2A(Agent-to-Agent) JSON-RPC 2.0 프로토콜**, 그리고 **Plan-and-Execute (Planner ➡️ Parallel Dispatcher ➡️ Synthesizer)** 패턴을 결합하여 분산 8대 전문 서브 에이전트와 실시간 스트림 워커를 조율하는 금융 특화 마이크로서비스 플랫폼입니다.

> 📚 **모듈별 및 기술 상세 문서는 [docs/README.md](docs/README.md)에서 확인하실 수 있습니다.**

---

## 🏛️ 시스템 아키텍처 (Mermaid Diagram)

모든 서비스는 독립된 Docker 컨테이너로 동작하며, `agent_shared_net` 공유 네트워크를 통해 동적으로 서로를 탐색하고 통신합니다.

```mermaid
graph TD
    User["👤 사용자 / 클라이언트"] -->|1. POST /api/v1/supervisor/invoke| App

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
            Grafana["📈 agent_grafana (Port: 23000)"]
        end

        %% Dynamic Discovery flow
        App -->|2. SSE Client & list_agent_cards| MCP
        MCP -.->|3. Probe /.well-known/agent-card.json| DataProc
        MCP -.->|3. Probe /.well-known/agent-card.json| WebSearch
        MCP -.->|3. Probe /.well-known/agent-card.json| Fundamental
        MCP -.->|3. Probe /.well-known/agent-card.json| Technical
        MCP -.->|3. Probe /.well-known/agent-card.json| Dart
        MCP -.->|3. Probe /.well-known/agent-card.json| Macro
        MCP -.->|3. Probe /.well-known/agent-card.json| BullBear
        MCP -.->|3. Probe /.well-known/agent-card.json| Risk

        %% A2A Task Delegation flow (Plan-and-Execute)
        App -->|4. A2A Parallel Dispatch| DataProc
        App -->|4. A2A Parallel Dispatch| WebSearch
        App -->|4. A2A Parallel Dispatch| Fundamental
        App -->|4. A2A Parallel Dispatch| Technical
        App -->|4. A2A Parallel Dispatch| Dart
        App -->|4. A2A Parallel Dispatch| Macro
        App -->|4. A2A Parallel Dispatch| BullBear
        App -->|4. A2A Parallel Dispatch| Risk

        %% Streaming & Persistence
        StreamWorker -->|1분봉 롤링 벌크 적재| DB
        DataProc -->|시세/지표 영속화 & 조회| DB

        %% Observability
        Prometheus -.->|Scrape /metrics| App
        Prometheus -.->|Scrape /metrics| DataProc
        Prometheus -.->|Scrape /metrics| Risk
        Grafana -->|Datasource| Prometheus
        Grafana -->|Datasource| Loki
    end
```

---

## 📂 디렉토리 및 폴더 구조 (Project Structure)

```text
agent_test/
├── 📚 docs/                    # 모듈별 통합 기술 문서 디렉토리
│   ├── app/                    # Orchestrator Server 상세 문서
│   ├── agent_server/           # 8대 Sub-Agents & Stream Worker 문서
│   ├── mcp_server/             # FastMCP Discovery Server 상세 문서
│   ├── shared_core/            # Shared Core Library 상세 문서
│   ├── monitoring/             # Monitoring Stack 상세 문서
│   ├── scripts/                # Operations Shell Scripts 상세 문서
│   ├── references/             # LangGraph 기술 참조 문서
│   ├── harness/                # 테스트 & 평가 하네스 엔지니어링 가이드
│   ├── architecture.md         # 전체 아키텍처 & 프로토콜 흐름도
│   └── README.md               # 문서 통합 목차 가이드
│
├── 🤖 app/                     # Orchestrator (Supervisor Plan-and-Execute)
│   ├── agents/                 # Planner, Parallel Dispatcher, Synthesizer, Supervisor
│   │   ├── planner.py          # [Planner] 의도 분석 및 실행 계획(DAG) 수립
│   │   ├── dispatcher.py       # [Dispatcher] asyncio.gather 기반 병렬 호출기
│   │   ├── synthesizer.py      # [Synthesizer] 결과 종합 및 리포트 생성
│   │   ├── supervisor.py       # Plan-and-Execute 메인 워크플로우
│   │   └── factory.py          # AgentFactory
│   ├── api/                    # /api/v1/supervisor/invoke, stream, info 엔드포인트
│   ├── core/                   # LLM Registry, MCP SSE 클라이언트
│   └── tests/                  # Pytest 유닛 및 통합 테스트 수트
│
├── 🗣️ agent_server/            # 8대 금융 전문 Sub-Agents & Background Worker
│   ├── agents/                 # A2A 웹 서비스 에이전트 모듈 (to_a2a)
│   │   ├── data_processing_agent.py  # 주식 데이터 취합 (Rule/LLM) & DB (Port: 28001)
│   │   ├── web_search_agent.py       # DuckDuckGo ReAct 웹 검색 (Port: 28003)
│   │   ├── fundamental_agent.py      # 재무제표 3표 & 밸류에이션 분석 (Port: 28004)
│   │   ├── technical_agent.py        # 차트 패턴 & 기술적 지표/신호 (Port: 28005)
│   │   ├── dart_disclosure_agent.py  # DART 전자공시 & 오버행 분석 (Port: 28006)
│   │   ├── macro_sector_agent.py     # 거시경제 & 섹터 트렌드 (Port: 28007)
│   │   ├── bull_bear_debate_agent.py # Bull vs Bear 토론 & 판사 판정 (Port: 28008)
│   │   └── risk_management_agent.py  # 100% Rule-Based 리스크 게이트키퍼 (Port: 28009)
│   ├── workers/                # 백그라운드 실시간 수집 워커 (No LLM)
│   │   └── stream_worker.py    # 한투 WebSocket 틱 수신 & 1분봉 롤링 DB 벌크 적재
│   └── core/                   # PostgreSQL async 세션 & SQLAlchemy ORM 모델
│
├── 🔌 mcp_server/              # Model Context Protocol (FastMCP Server)
│   ├── tools/                  # list_agent_cards (8대 에이전트 동적 탐색 도구)
│   └── server.py               # FastMCP SSE 전송 서버 진입점 (Port: 28002)
│
├── 📦 shared_core/             # 공통 공유 라이브러리 (Shared Core Package)
│   └── src/shared_core/
│       ├── base_node.py        # LangGraph BaseNode 추상화 (ABC, DI, 구조화 로깅)
│       ├── logger.py           # UTF-8 지원 Structlog 로거
│       └── prompt.py           # YAML 프롬프트 로더
│
├── 📊 monitoring/              # 관찰 가능성 모니터링 스택
│   ├── grafana/                # Grafana 대시보드 (Port: 23000)
│   ├── prometheus.yml          # Prometheus 메트릭 수집 (Port: 29090)
│   └── promtail-config.yaml    # Loki 컨테이너 로그 수집
│
├── 🚀 start.sh                 # 전체 서비스 원클릭 시작 스크립트
└── 🛑 stop.sh                  # 전체 서비스 원클릭 종료 스크립트
```

---

## 📍 서비스 포트 매핑 (Service Ports)

| 모듈 명 | 서비스 역할 | 호스트 포트 | 주요 기능 |
| :--- | :--- | :--- | :--- |
| **`app`** | Orchestrator Server | `28000` | Supervisor Plan-and-Execute REST API |
| **`data_processing_agent`** | Data Processing Sub-Agent | `28001` | LangGraph 시세 수집 & 정제 & DB 적재 |
| **`mcp_server`** | FastMCP Discovery Server | `28002` | `list_agent_cards` SSE 동적 탐색 |
| **`web_search_agent`** | Web Search Sub-Agent | `28003` | DuckDuckGo 실시간 웹 검색 |
| **`fundamental_agent`** | Fundamental Sub-Agent | `28004` | 재무 3표 & 밸류에이션(PER/PBR/ROE) |
| **`technical_agent`** | Technical Sub-Agent | `28005` | 차트 패턴 & 지지/저항선 & 매매 신호 |
| **`dart_disclosure_agent`**| DART Sub-Agent | `28006` | 전자공시 & 오버행/희석률 분석 |
| **`macro_sector_agent`** | Macro & Sector Sub-Agent | `28007` | 글로벌 거시경제 & 섹터 상대강도 |
| **`bull_bear_debate_agent`**| Bull vs Bear Sub-Agent | `28008` | 다자간 토론 & 판사 최종 투자 의견 |
| **`risk_management_agent`** | Risk Management Sub-Agent| `28009` | 100% Rule-Based 비중 한도 & 손절선 |
| **`stream_worker`** | Ingestion Daemon | N/A | 한투증권 WebSocket 실시간 틱 수집 |
| **`postgres`** | PostgreSQL Database | `5432` | 시계열 1분봉 & 일간 정제 지표 영속화 |
| **`prometheus`** | Prometheus Metrics | `29090` | 전체 서비스 HTTP 메트릭 스크랩 |
| **`grafana`** | Grafana UI | `23000` | 로그 & 메트릭 통합 대시보드 (`admin`/`admin`) |

---

## 💡 빠른 시작 (Quick Start)

### 1. 환경 설정
```bash
cp .env.example .env
```

### 2. 전체 서비스 실행
```bash
./start.sh
```

### 3. API 호출 테스트
```bash
# 삼성전자 종합 분석 및 리스크 심의 요청
curl -X POST http://localhost:28000/api/v1/supervisor/invoke \
  -H "Content-Type: application/json" \
  -d '{"message": "삼성전자(005930) 종합 분석 및 투자 심의해줘"}'
```

### 4. 하네스 단위 테스트 실행
```bash
cd app && uv run pytest
```
