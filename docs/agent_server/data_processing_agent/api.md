# 🔌 Data Processing Sub-Agent API 명세서

Data Processing Sub-Agent (`agent_data_processing_server`)가 제공하는 HTTP 및 A2A JSON-RPC 2.0 엔드포인트 명세입니다.
본 서비스는 Google ADK의 `to_a2a(data_processing_agent)` 변환 함수를 통해 포장된 Starlette/FastAPI 애플리케이션으로 동작합니다.

---

## 1. 기본 정보 (Base Information)

- **Base URL**: `http://agent_data_processing_server:28001` (또는 `http://localhost:28001`)
- **A2A Adapter**: `google.adk.a2a.utils.agent_to_a2a.to_a2a`
- **Protocol**: HTTP / Google ADK A2A JSON-RPC 2.0
- **Content-Type**: `application/json`

---

## 2. 엔드포인트 목록 (Endpoints)

### 2.1. Agent Card 조회 (`GET /.well-known/agent-card.json`)
- **설명**: `to_a2a(agent)` 유틸리티에 의해 자동 서빙되는 에이전트 능력(Capabilities) 및 통신 메타데이터 카드입니다.
- **Method**: `GET`
- **Path**: `/.well-known/agent-card.json`
- **Response 예시 (`200 OK`)**:
  ```json
  {
    "name": "data_processing_agent",
    "description": "LangGraph 기반 데이터 정제 및 포맷팅 에이전트",
    "url": "http://agent_data_processing_server:28001"
  }
  ```

---

### 2.2. A2A Task 위임 및 데이터 정제 실행 (`POST /`)
- **설명**: 원시 텍스트 및 입력 데이터를 전달받아 `to_a2a` 인터페이스를 거쳐 정제 템플릿을 적용한 결과를 반환합니다.
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
        "content": "수신 데이터 노이즈 제거 및 요약 요청"
      }
    },
    "id": "req-dp-001"
  }
  ```
- **Response Payload 예시**:
  ```json
  {
    "jsonrpc": "2.0",
    "result": {
      "event": {
        "author": "data_processing_agent",
        "content": {
          "role": "model",
          "parts": [
            {
              "text": "[data_processing] 수신 데이터 노이즈 제거 및 요약 요청"
            }
          ]
        }
      }
    },
    "id": "req-dp-001"
  }
  ```

---

### 2.3. Prometheus 메트릭 수집 (`GET /metrics`)
- **설명**: `to_a2a(agent)` 웹 애플리케이션에 Prometheus Instrumentator가 추가되어 제공되는 메트릭 엔드포인트입니다.
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
