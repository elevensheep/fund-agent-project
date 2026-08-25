# 🔍 Web Search Sub-Agent (`web_search_agent`)

본 문서는 LangGraph ReAct 기반으로 웹 검색 기능을 수행하는 **Web Search Sub-Agent**의 아키텍처 및 구현 가이드입니다.

---

## 1. 개요

`web_search_agent`는 사용자의 질문이나 오케스트레이터(Supervisor)의 지시에 따라 최신 웹 정보를 동적으로 탐색하고 답변을 생성하는 원격 서브 에이전트입니다.
`duckduckgo-search` 패키지를 활용하여 별도의 외부 검색 API 키 없이도 DuckDuckGo 엔진 기반 검색 기능을 제공하며, Google ADK의 **`to_a2a` 변환 유틸리티**를 적용하여 A2A(Agent-to-Agent) JSON-RPC 2.0 호환 웹 서비스로 제공됩니다.

---

## 2. 주요 기능 및 특징

- **DuckDuckGo Web Search Tool**:
  - `web_search(query: str, max_results: int = 5)` 도구를 내장하여 실시간 웹 검색 결과(제목, 요약 내용, 링크 URL)를 수집합니다.
- **LangGraph ReAct Agent Architecture**:
  - `create_react_agent` 빌더로 LLM과 Search Tool을 바인딩하여 자율적으로 검색 필요 여부를 판단하고 추론하는 ReAct 루프 동작.
- **Google ADK `to_a2a` 변환 래퍼**:
  - `from google.adk.a2a.utils.agent_to_a2a import to_a2a`를 사용하여 `SafeLangGraphAgent` 인스턴스를 표준 A2A Starlette/FastAPI 웹 애플리케이션으로 자동 변환.
  - 변환된 `a2a_app`은 `/.well-known/agent-card.json` 엔드포인트 및 A2A JSON-RPC 2.0 메세지 처리 기능을 내장합니다.
- **SafeLangGraphAgent 세이프가드**:
  - `InvocationContext` 기반의 `thread_id` 세션 관리 및 `Event` 파싱 지원.
  - API 키 부재 시 `FakeMessagesListChatModel` (Mock LLM) 모드로 안전한 폴백 실행.
- **Observability & Health**:
  - FastAPI Prometheus Instrumentator를 통한 `/metrics` 제공.

---

## 3. 코드 구현 구조 예시 (`to_a2a` 사용 방식)

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.langgraph_agent import LangGraphAgent
from langgraph.prebuilt import create_react_agent
from prometheus_fastapi_instrumentator import Instrumentator

# 1. LangGraph ReAct 에이전트 및 SafeLangGraphAgent 정의
graph = create_react_agent(model=llm, tools=[web_search], prompt=system_prompt)
agent = SafeLangGraphAgent(
    name="web_search_agent",
    description="DuckDuckGo 기반 웹 검색 에이전트",
    graph=graph,
)

# 2. to_a2a() 변환을 통해 A2A 호환 Starlette/FastAPI 애플리케이션 생성
a2a_app = to_a2a(agent)

# 3. Prometheus 모니터링 메트릭 바인딩
Instrumentator().instrument(a2a_app).expose(a2a_app)

# Uvicorn entrypoint
app = a2a_app
```

---

## 4. 기술 스택 및 요구사항

- **Language & Framework**: Python 3.12, FastAPI / Starlette
- **Agent Framework**: LangGraph, LangChain Core, Google ADK (`google-adk`)
- **A2A Adapter**: `google.adk.a2a.utils.agent_to_a2a.to_a2a`
- **Search Library**: `duckduckgo-search` (`pip install duckduckgo-search`)
- **포트 및 서비스명**:
  - **Port**: `28003`
  - **Docker Service Name**: `agent_web_search_server`

---

## 5. 실행 및 테스트

### 5.1. 의존성 설치
```bash
pip install duckduckgo-search
```

### 5.2. 에이전트 독립 실행
```bash
uvicorn agent_server.agents.web_search_agent:app --host 0.0.0.0 --port 28003
```
