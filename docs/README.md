# Agent Ecosystem Documentation Hub

Agent Ecosystem 프로젝트의 전체 문서 목차 및 하네스 엔지니어링 가이드 안내입니다.

---

## 📚 문서 목차 (Table of Contents)

1. [🏛️ 시스템 아키텍처 (Architecture)](architecture.md)
   - 전체 시스템 구조, 서비스 구성, 도커 네트워크, MCP 및 A2A 프로토콜 흐름도
2. [🧪 하네스 엔지니어링 & 테스트 가이드 (Testing Harness)](harness/README.md)
   - Unit/Integration/Contract/Observability 6단계 테스트 및 평가 하네스 명세
3. [🎨 프론트엔드 아키텍처 & 기술 스택 가이드 (Frontend Guide)](frontend/README.md)
   - Next.js 14+, Tailwind CSS, TradingView Lightweight Charts, 컴포넌트 아키텍처 및 Docker 배포
4. [🔌 프론트엔드 연동 & 통신 하네스 (Frontend Harness)](harness/frontend_harness.md)
   - 백엔드 REST/SSE API 계약, DAG 단계 추적기, Mock 데이터 Fixture 및 스트리밍 훅 명세
5. [🤖 오케스트레이터 서버 문서 (`app`)](app/README.md)
   - Supervisor Client Server 구조, Plan-and-Execute 아키텍처, API 엔드포인트 spec 및 Pytest 테스트
6. [🗣️ 원격 서브 에이전트 서버 문서 (`agent_server`)](agent_server/README.md)
   - 8대 금융 서브 에이전트 및 KIS 실시간 스트림 워커 사양 & A2A 명세
7. [🔌 MCP 서버 문서 (`mcp_server`)](mcp_server/README.md)
   - FastMCP SSE 기반 Model Context Protocol 서버 및 에이전트 동적 탐색 도구 (`list_agent_cards`)
8. [📦 공통 공유 라이브러리 문서 (`shared_core`)](shared_core/README.md)
   - LangGraph 노드 추상화 객체(`base_node.py`), UTF-8 구조화 로그(`logger.py`), YAML 프롬프트 로더(`prompt.py`)
9. [📊 모니터링 스택 문서 (`monitoring`)](monitoring/README.md)
   - Prometheus 메트릭 수집, Loki + Promtail 로그 수집, Grafana 대시보드 연동
10. [📜 운영 관리 스크립트 문서 (`scripts`)](scripts/README.md)
    - 각 모듈 및 전체 시스템 실행/종료/업데이트 쉘 스크립트 사용법
11. [📝 기술 참조 (References)](references/langgraph_reference.md)
    - LangGraph 버전 정보 및 API Signature 참조 가이드
12. [🌿 Git 컨벤션 가이드 (Git Convention)](git_convention.md)
    - 브랜치 전략, Conventional Commits 메시지 규격, PR 및 코드 리뷰 가이드라인

---

## 🛠️ 모듈별 요약 및 포트 매핑

| 모듈 명 | 설명 | 주요 기술 스택 | 포트 | 문서 링크 |
| :--- | :--- | :--- | :--- | :--- |
| **`app`** | Central Supervisor Agent & API Server | FastAPI, Pydantic, LangChain | `28000` | [app/README.md](app/README.md) |
| **`agent_server`** | 8대 금융 전문 Sub-Agents & Stream Worker | Google ADK `to_a2a`, LangGraph, PostgreSQL | `28001`, `28003~28009` | [agent_server/README.md](agent_server/README.md) |
| **`mcp_server`** | FastMCP Dynamic Agent Card Discovery | FastMCP, SSE Protocol | `28002` | [mcp_server/README.md](mcp_server/README.md) |
| **`shared_core`** | Shared Utilities (BaseNode, Logging, Prompts) | BaseNode (ABC/DI), Structlog, PyYAML | N/A | [shared_core/README.md](shared_core/README.md) |
| **`monitoring`** | Observability (Metrics & Logs) | Prometheus, Loki, Grafana | `23000`, `29090` | [monitoring/README.md](monitoring/README.md) |
| **`frontend`** | Financial Dashboard Web Client | Next.js 14+, Tailwind, Lightweight Charts | `3000` | [frontend/README.md](frontend/README.md) |
| **`harness`** | Test & Frontend Harness Framework | Pytest, Next.js/React Contract, Mock SSE | N/A | [harness/README.md](harness/README.md) |
| **`scripts`** | Operation Shell Scripts | Bash Shell | N/A | [scripts/README.md](scripts/README.md) |
| **`git_convention`** | Git Branching & Commit Message Convention | Git Flow, Conventional Commits | N/A | [git_convention.md](git_convention.md) |

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
  -d '{"message": "삼성전자(005930) 종합 분석 및 투자 심의해줘"}'
```

### 4. 하네스 자동 검증 테스트
```bash
# Pytest 단위 테스트 (Orchestrator & Sub-Agents)
cd app && uv run pytest
cd ../agent_server && uv run pytest

# A2A Agent Card 프로빙 계약 검증
curl -s http://localhost:28001/.well-known/agent-card.json | jq .
curl -s http://localhost:28003/.well-known/agent-card.json | jq .
```

### 5. 서비스 종료
```bash
./stop.sh
```
