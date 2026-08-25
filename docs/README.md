# Agent Ecosystem Documentation Hub

Agent Ecosystem 프로젝트의 전체 문서 목차 및 하네스 엔지니어링 가이드 안내입니다.

---

## 📚 문서 목차 (Table of Contents)

1. [🏛️ 시스템 아키텍처 (Architecture)](architecture.md)
   - 전체 시스템 구조, 서비스 구성, 도커 네트워크, MCP 및 A2A 프로토콜 흐름도
2. [🧪 하네스 엔지니어링 & 테스트 가이드 (Testing Harness)](harness/README.md)
   - Unit/Integration/Contract/Observability 5단계 테스트 및 평가 하네스 명세
3. [🤖 오케스트레이터 서버 문서 (`app`)](app/README.md)
   - Supervisor Client Server 구조, 계층형 아키텍처, API 엔드포인트 spec 및 Pytest 테스트
4. [🗣️ 원격 서브 에이전트 서버 문서 (`agent_server`)](agent_server/README.md)
   - [Data Processing Agent](agent_server/data_processing_agent/README.md) & [Web Search Agent](agent_server/web_search_agent/README.md) 사양 및 A2A API 명세
5. [🔌 MCP 서버 문서 (`mcp_server`)](mcp_server/README.md)
   - FastMCP SSE 기반 Model Context Protocol 서버 및 에이전트 동적 탐색 도구 (`list_agent_cards`)
6. [📦 공통 공유 라이브러리 문서 (`shared_core`)](shared_core/README.md)
   - UTF-8 구조화 로그 관리자(`logger.py`) 및 YAML 프롬프트 로더(`prompt.py`)
7. [📊 모니터링 스택 문서 (`monitoring`)](monitoring/README.md)
   - Prometheus 메트릭 수집, Loki + Promtail 로그 수집, Grafana 대시보드 연동
8. [📜 운영 관리 스크립트 문서 (`scripts`)](scripts/README.md)
   - 각 모듈 및 전체 시스템 실행/종료/업데이트 쉘 스크립트 사용법
9. [📝 기술 참조 (References)](references/langgraph_reference.md)
   - LangGraph 버전 정보 및 API Signature 참조 가이드

---

## 🛠️ 모듈별 요약 및 포트 매핑

| 모듈 명 | 설명 | 주요 기술 스택 | 포트 | 문서 링크 |
| :--- | :--- | :--- | :--- | :--- |
| **`app`** | Central Supervisor Agent & API Server | FastAPI, Pydantic, LangChain | `28000` | [app/README.md](app/README.md) |
| **`agent_server`** | Data Processing & Web Search Sub-Agents | Google ADK `to_a2a`, LangGraph | `28001`, `28003` | [agent_server/README.md](agent_server/README.md) |
| **`mcp_server`** | FastMCP Dynamic Agent Card Discovery | FastMCP, SSE Protocol | `28002` | [mcp_server/README.md](mcp_server/README.md) |
| **`shared_core`** | Shared Utilities (Logging, Prompts) | Structlog, PyYAML | N/A | [shared_core/README.md](shared_core/README.md) |
| **`monitoring`** | Observability (Metrics & Logs) | Prometheus, Loki, Grafana | `23000`, `29090` | [monitoring/README.md](monitoring/README.md) |
| **`scripts`** | Operation Shell Scripts | Bash Shell | N/A | [scripts/README.md](scripts/README.md) |
| **`harness`** | Test & Evaluation Harness Framework | Pytest, A2A/MCP Contract, Mock LLM | N/A | [harness/README.md](harness/README.md) |

---

## 🚀 빠른 시작 가이드 (Quick Start)

### 1. 환경 변수 설정
```bash
cp .env.example .env
```

### 2. 전체 서비스 실행
```bash
./start.sh
```

### 3. API 호출 테스트
```bash
curl -X POST http://localhost:28000/api/v1/supervisor/invoke \
  -H "Content-Type: application/json" \
  -d '{"message": "2026년 에이전트 기술 동향을 웹에서 검색하고 정제해줘"}'
```

### 4. 하네스 자동 검증 테스트
```bash
# Pytest 단위 테스트
cd app && uv run pytest

# A2A Agent Card 프로빙 계약 검증
curl -s http://localhost:28001/.well-known/agent-card.json | jq .
curl -s http://localhost:28003/.well-known/agent-card.json | jq .
```

### 5. 서비스 종료
```bash
./stop.sh
```
