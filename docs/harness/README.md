# 🧪 Test & Evaluation Harness Engineering Guide

본 문서는 Agent Ecosystem의 **하네스 엔지니어링(Harness Engineering) 관점의 검증, 테스트 및 평가 프레임워크 명세서**입니다.
다중 에이전트 오케스트레이션 시스템의 신뢰성, 계약(Contract) 준수 여부, 오프라인 결정론적 테스트 및 관찰 가능성을 자동 검증하기 위한 가이드를 제공합니다.

---

## 1. 하네스 엔지니어링 아키텍처 (Harness Architecture)

본 시스템의 검증 하네스는 5단계 레이어로 구성됩니다.

```mermaid
graph TD
    subgraph Test & Evaluation Harness
        Unit["1️⃣ Unit Test Harness<br/>(pytest app/tests - Isolated Logic)"]
        Contract["2️⃣ Protocol Contract Harness<br/>(A2A JSON-RPC 2.0 & MCP SSE Spec)"]
        MockLLM["3️⃣ Offline Mock LLM Harness<br/>(FakeMessagesListChatModel Safeguard)"]
        Observability["4️⃣ Observability Assertion Harness<br/>(task.* / artifact.* Logs & /metrics)"]
        E2E["5️⃣ E2E Integration Harness<br/>(curl /api/v1/supervisor/invoke)"]
    end

    Unit --> Contract
    Contract --> MockLLM
    MockLLM --> Observability
    Observability --> E2E
```

---

## 2. 레이어별 검증 명세 (Harness Layers Spec)

### 2.1. Offline Mock LLM Harness (오프라인 검증 하네스)
- **목적**: 외부 LLM (OpenAI, Anthropic, Google) API 키나 네트워크 연결 없이도 하네스가 독립 구동되는 오프라인 샌드박스 검증.
- **메커니즘**:
  - `.env` 키 미설정 시 `LLMRegistry`가 `FakeMessagesListChatModel` 인스턴스를 자동으로 생성.
  - `responses=[AIMessage(content="[Mock] Response")]` 형태의 미리 정의된 결정론적 시퀀스로 에이전트 제어 로직 검증.
- **Pytest 구동 예시**:
  ```python
  fake_llm = FakeMessagesListChatModel(responses=[AIMessage(content="Mock Test Output")])
  supervisor = SupervisorAgent(llm=fake_llm, remote_agents={})
  res = await supervisor.ainvoke({"message": "Test Message"})
  assert res["output"] == "Mock Test Output"
  ```

---

### 2.2. Protocol Contract Harness (계약 검증 하네스)

#### A. A2A (Agent-to-Agent) JSON-RPC 2.0 Contract
- **검증 표준**: Google ADK `to_a2a` 어댑터가 노출하는 REST 및 JSON-RPC 규격.
- **필수 계약 항목**:
  1. `GET /.well-known/agent-card.json` -> HTTP 200 OK, JSON 객체 반환 (`name`, `description`, `url`).
  2. `POST /` -> JSON-RPC 2.0 `SendMessage` 처리 및 `event` 객체 응답.

#### B. MCP (Model Context Protocol) SSE Contract
- **검증 표준**: FastMCP SSE 전송 규격 및 `list_agent_cards` 도구 파싱.
- **필수 계약 항목**:
  1. `GET /sse` -> SSE Server-Sent Event 스트림 연결.
  2. `list_agent_cards` 실행 -> 서브 에이전트 Card 메타데이터 리스트 수집.

---

### 2.3. Observability Assertion Harness (로그/메트릭 하네스)
- **로그 명명 표준 (Log Assertion)**:
  - 태스크 실행 로그: `task.<agent_name>.<event>` (예: `task.data_processing_agent.received_message`)
  - 결과 아티팩트 로그: `artifact.<agent_name>.<event>` (예: `artifact.langchain_agent.event_created`)
- **메트릭 엔드포인트 수집 (Metric Assertion)**:
  - 모든 서비스의 `GET /metrics`가 HTTP 200 OK 및 Prometheus 텍스트 메트릭을 반환해야 함.

---

## 3. 하네스 자동화 실행 명령어 (Automated Harness Execution)

### 3.1. Pytest 단위 및 단위 팩토리 테스트 실행
```bash
cd app
uv run pytest
```

### 3.2. A2A & MCP 프로토콜 계약 검증 (`curl` 하네스 스크립트)

#### 1) Sub-Agent Card 검증
```bash
curl -s http://localhost:28001/.well-known/agent-card.json | jq .
curl -s http://localhost:28003/.well-known/agent-card.json | jq .
```

#### 2) Supervisor End-to-End 하네스 검증
```bash
curl -X POST http://localhost:28000/api/v1/supervisor/invoke \
  -H "Content-Type: application/json" \
  -d '{"message": "웹 검색 결과 정제 테스트"}' | jq .
```

#### 3) Monitoring & Metrics 검증
```bash
curl -s http://localhost:28000/metrics | grep http_requests
curl -s http://localhost:28001/metrics | grep http_requests
curl -s http://localhost:28003/metrics | grep http_requests
```

---

## 4. 하네스 엔지니어링 체크리스트 (Harness Checklist)

- [x] **Zero Dependency Execution**: API 키가 없을 때 Mock LLM으로 자동 세이프가드 전환되는가?
- [x] **Agent Card Discovery**: MCP Server가 모든 원격 에이전트의 `/.well-known/agent-card.json`을 프로빙할 수 있는가?
- [x] **A2A Protocol Compliance**: 서브 에이전트들이 `to_a2a` 래퍼를 통해 JSON-RPC 2.0 표준 이벤트를 반환하는가?
- [x] **Log & Metric Tracing**: 모든 주요 에이전트 이벤트가 `task.*` 및 `artifact.*` 형식을 준수하고 `/metrics`가 노출되는가?
