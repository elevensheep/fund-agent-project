# ⚙️ Data Processing Sub-Agent (`data_processing_agent`)

본 문서는 데이터 정제, 텍스트 표준화 및 파이프라인 처리를 담당하는 **Data Processing Sub-Agent**의 아키텍처 및 구현 가이드입니다.

---

## 1. 개요

`data_processing_agent`는 다른 에이전트(예: `web_search_agent`)가 수집한 원시 데이터(Raw Text)나 클라이언트의 입력을 받아 정제, 포맷팅, 노이즈 제거 등의 데이터 전처리 작업을 수행하는 경량화 서브 에이전트입니다.
LangGraph의 `StateGraph` 구조를 사용하여 빠른 처리 속도와 예측 가능한 템플릿 응답을 보장하며, Google ADK의 **`to_a2a` 변환 유틸리티**를 사용하여 A2A 호환 서버로 동작합니다.

---

## 2. 주요 기능 및 특징

- **LangGraph StateGraph 노드 구조**:
  - 복잡한 LLM 자율 추론 대신 지정된 템플릿 규격에 맞추어 빠른 정제 작업을 수행하는 결정론적 그래프 노드 구성.
- **YAML 프롬프트 템플릿 연동**:
  - `prompts/data_processing.yml` 프롬프트를 동적으로 로드하여 수신 데이터에 `[data_processing] {content}` 표준 정제 파이프라인을 적용.
- **Google ADK `to_a2a` 변환 래퍼**:
  - `from google.adk.a2a.utils.agent_to_a2a import to_a2a`를 활용해 LangGraphAgent 인스턴스를 Starlette/FastAPI 웹 앱으로 자동 변환.
  - 변환된 `a2a_app`을 통해 `/.well-known/agent-card.json` 엔드포인트 제공 및 A2A JSON-RPC 2.0 태스크 수신 처리.
- **UTF-8 지원 구조화 로깅**:
  - `shared_core.logger`를 이용한 `task.data_processing_agent.received_message` 및 `artifact.data_processing_agent.message_created` 메트릭 트레이스 로그 전송.
- **Prometheus 메트릭**:
  - Prometheus Instrumentator 메트릭 스크랩 지원 (`/metrics`).

---

## 3. 코드 구현 구조 예시 (`to_a2a` 사용 방식)

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.langgraph_agent import LangGraphAgent
from langgraph.graph import StateGraph, START, END
from prometheus_fastapi_instrumentator import Instrumentator

# 1. LangGraph StateGraph 및 Agent 생성
graph_builder = StateGraph(State)
graph_builder.add_node("data_processing", data_processing_node)
graph_builder.add_edge(START, "data_processing")
graph_builder.add_edge("data_processing", END)

data_processing_graph = graph_builder.compile()
data_processing_agent = LangGraphAgent(
    name="data_processing_agent",
    description="Data processing agent powered by LangGraph",
    graph=data_processing_graph,
)

# 2. to_a2a() 변환을 통한 A2A 애플리케이션 빌드
a2a_app = to_a2a(data_processing_agent)

# 3. Prometheus 모니터링 바인딩
Instrumentator().instrument(a2a_app).expose(a2a_app)

# Uvicorn entrypoint
app = a2a_app
```

---

## 4. 기술 스택 및 요구사항

- **Language & Framework**: Python 3.12, FastAPI / Starlette
- **Agent Framework**: LangGraph, Google ADK (`google-adk`)
- **A2A Adapter**: `google.adk.a2a.utils.agent_to_a2a.to_a2a`
- **포트 및 서비스명**:
  - **Port**: `28001`
  - **Docker Service Name**: `agent_data_processing_server`

---

## 5. 실행 및 테스트

### 5.1. 에이전트 독립 실행
```bash
uvicorn agent_server.agents.data_processing_agent:app --host 0.0.0.0 --port 28001
```
