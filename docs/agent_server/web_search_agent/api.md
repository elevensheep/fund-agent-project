# 🔌 Web Search Sub-Agent API 명세서

Web Search Sub-Agent (`agent_web_search_server`)가 제공하는 HTTP 및 A2A JSON-RPC 2.0 엔드포인트 명세입니다.
본 서비스는 Google ADK의 `to_a2a(agent)` 변환 함수를 통해 생성된 Starlette/FastAPI 애플리케이션으로 동작합니다.

---

## 1. 기본 정보 (Base Information)

- **Base URL**: `http://agent_web_search_server:28003` (또는 `http://localhost:28003`)
- **A2A Adapter**: `google.adk.a2a.utils.agent_to_a2a.to_a2a`
- **Protocol**: HTTP / Google ADK A2A JSON-RPC 2.0
- **Content-Type**: `application/json`

---

## 2. 엔드포인트 목록 (Endpoints)

### 2.1. Agent Card 조회 (`GET /.well-known/agent-card.json`)
- **설명**: `to_a2a(agent)`에 의해 자동 서빙되는 에이전트 능력(Capabilities) 및 통신 메타데이터 카드입니다. MCP Server의 동적 탐색 도구(`list_agent_cards`)에서 자동 수집됩니다.
- **Method**: `GET`
- **Path**: `/.well-known/agent-card.json`
- **Response 예시 (`200 OK`)**:
  ```json
  {
    "name": "web_search_agent",
    "description": "DuckDuckGo 기반 웹 검색 및 정제 기능을 제공하는 LangChain ReAct 에이전트",
    "url": "http://agent_web_search_server:28003",
    "tools": [
      {
        "name": "web_search",
        "description": "DuckDuckGo 엔진을 사용하여 입력 키워드에 대한 최신 웹 정보를 검색합니다."
      }
    ]
  }
  ```

---

### 2.2. A2A Task 위임 및 실행 (`POST /`)
- **설명**: Supervisor 에이전트로부터 메시지 및 태스크를 위임받아 `to_a2a` 인터페이스를 통해 ReAct 루프 웹 검색을 수행하고 응답 이벤트를 반환합니다.
- **Method**: `POST`
- **Path**: `/`
- **Request Payload 예시 (A2A JSON-RPC 2.0)**:
  ```json
  {
    "jsonrpc": "2.0",
    "method": "SendMessage",
    "params": {
      "message": {
        "role": "user",
        "content": "2026년 인공지능 에이전트 트렌드에 대해 검색해줘"
      }
    },
    "id": "req-ws-001"
  }
  ```
- **Response Payload 예시**:
  ```json
  {
    "jsonrpc": "2.0",
    "result": {
      "event": {
        "author": "web_search_agent",
        "content": {
          "role": "model",
          "parts": [
            {
              "text": "웹 검색 결과, 2026년 AI 에이전트 트렌드는 MCP 및 A2A 다중 에이전트 오케스트레이션이 핵심으로..."
            }
          ]
        }
      }
    },
    "id": "req-ws-001"
  }
  ```

---

### 2.3. Prometheus 메트릭 수집 (`GET /metrics`)
- **설명**: `to_a2a(agent)` 애플리케이션에 `prometheus_fastapi_instrumentator`가 바인딩되어 메트릭을 제공합니다.
- **Method**: `GET`
- **Path**: `/metrics`
- **Response**: OpenMetrics / Prometheus 텍스트 포맷

---

### 2.4. Health Check (`GET /health`)
- **설명**: 컨테이너 헬스 상태 확인.
- **Method**: `GET`
- **Path**: `/health`
- **Response 예시 (`200 OK`)**:
  ```json
  {
    "status": "ok"
  }
  ```
