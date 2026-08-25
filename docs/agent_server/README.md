# 🗣️ Remote Sub-Agents Server (`agent_server`) 문서

본 문서는 **Agent Ecosystem의 원격 서브 에이전트 서비스인 `agent_server`**의 아키텍처, 서브 에이전트 종류, A2A 프로토콜 및 하네스 엔지니어링 가이드를 설명합니다.

---

## 1. 개요

`agent_server` 모듈은 Supervisor 에이전트로부터 위임받은 개별 도구 및 전문 태스크를 독립적으로 수행하는 원격 A2A(Agent-to-Agent) 서브 에이전트들의 집합입니다.
Google ADK의 `to_a2a` 유틸리티(`from google.adk.a2a.utils.agent_to_a2a import to_a2a`)를 적용하여 각 에이전트를 표준 JSON-RPC 2.0 및 HTTP 프로토콜 엔드포인트로 외부에 노출시킵니다.

---

## 2. 서브 에이전트 개별 문서 링크 (Sub-Agents Documentation)

각 서브 에이전트의 상세 사양 및 API 명세서는 전용 디렉토리 문서에서 확인하실 수 있습니다.

| 서브 에이전트 명 | 모듈 경로 | 포트 | 개별 가이드 | API 명세서 |
| :--- | :--- | :--- | :--- | :--- |
| **Data Processing Agent** | `agents/data_processing_agent.py` | `28001` | [README](data_processing_agent/README.md) | [api.md](data_processing_agent/api.md) |
| **Web Search Agent** | `agents/web_search_agent.py` | `28003` | [README](web_search_agent/README.md) | [api.md](web_search_agent/api.md) |

---

## 3. 디렉토리 및 파일 구조

```text
agent_server/
├── agents/                           # 에이전트 구현 모듈
│   ├── data_processing_agent.py      # 데이터 정제 에이전트 (Port: 28001)
│   ├── web_search_agent.py           # Web 검색 에이전트 (Port: 28003)
│   └── prompts/                      # 에이전트 YAML 프롬프트 정의
│       ├── data_processing.yml       # Data Processing 템플릿 프롬프트
│       └── web_search.yml            # Web Search System Prompt
├── core/                             # 전역 설정 및 LLM 레지스트리
│   ├── config.py                     # Settings 모듈 (Pydantic BaseSettings)
│   └── llm.py                        # LLM Registry 및 Mock LLM 래퍼
├── Dockerfile                        # 도커 이미지 빌드 정의
├── docker-compose.yml                # 서브 에이전트 도커 서비스 스펙
└── pyproject.toml                    # uv 및 의존성 패키지 명세
```

---

## 4. 원격 서브 에이전트 사양 요약

### 4.1. Data Processing Sub-Agent (`agents/data_processing_agent.py`)
- **실행 포트**: `28001`
- **컨테이너 서비스 명**: `agent_data_processing_server`
- **주요 기능**:
  - LangGraph `StateGraph`를 사용하여 결정론적 데이터 정제 노드 구성.
  - 수신된 메시지에 `prompts/data_processing.yml`의 템플릿(`[data_processing] {content}`)을 적용하여 반환.
- **Agent Card 엔드포인트**: `GET http://agent_data_processing_server:28001/.well-known/agent-card.json`
- 📖 [상세 README](data_processing_agent/README.md) | 🔌 [API 명세](data_processing_agent/api.md)

### 4.2. Web Search Sub-Agent (`agents/web_search_agent.py`)
- **실행 포트**: `28003`
- **컨테이너 서비스 명**: `agent_web_search_server`
- **주요 기능**:
  - LangGraph `create_react_agent` 기반 ReAct 자율 추론 에이전트.
  - `web_search`: DuckDuckGo 엔진 기반 실시간 웹 검색 도구 (`duckduckgo-search`).
  - API 키 부재 시 `FakeMessagesListChatModel` (Mock LLM) 세이프가드 동작.
- **Agent Card 엔드포인트**: `GET http://agent_web_search_server:28003/.well-known/agent-card.json`
- 📖 [상세 README](web_search_agent/README.md) | 🔌 [API 명세](web_search_agent/api.md)

---

## 5. A2A 서버 구성 및 테스트 하네스

각 서브 에이전트는 `to_a2a(agent)` 함수를 통해 Starlette/FastAPI 애플리케이션으로 포장되며, `prometheus_fastapi_instrumentator`를 통해 수집 엔드포인트를 노출합니다.

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a

a2a_app = to_a2a(agent)
Instrumentator().instrument(a2a_app).expose(a2a_app)
```

- **Agent Card 하네스 테스트**: `curl http://localhost:28001/.well-known/agent-card.json`
- **메트릭 수집 검증**: `curl http://localhost:28001/metrics`
