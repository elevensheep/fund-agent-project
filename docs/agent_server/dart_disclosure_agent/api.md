# 🔌 DART Disclosure Sub-Agent API 명세서

DART Disclosure Sub-Agent (`agent_dart_disclosure_server`)가 제공하는 HTTP 및 A2A JSON-RPC 2.0 엔드포인트 명세입니다.
본 서비스는 Google ADK의 `to_a2a(dart_disclosure_agent)` 변환 함수를 통해 생성된 Starlette/FastAPI 애플리케이션으로 동작합니다.

---

## 1. 기본 정보 (Base Information)

- **Base URL**: `http://agent_dart_disclosure_server:28006` (또는 `http://localhost:28006`)
- **A2A Adapter**: `google.adk.a2a.utils.agent_to_a2a.to_a2a`
- **Protocol**: HTTP / Google ADK A2A JSON-RPC 2.0
- **Content-Type**: `application/json`

---

## 2. 엔드포인트 목록 (Endpoints)

### 2.1. Agent Card 조회 (`GET /.well-known/agent-card.json`)
- **Method**: `GET`
- **Path**: `/.well-known/agent-card.json`
- **Response 예시 (`200 OK`)**:
  ```json
  {
    "name": "dart_disclosure_agent",
    "description": "DART 전자공시 실시간 수집 및 기업 이벤트 호악재 분석 에이전트",
    "url": "http://agent_dart_disclosure_server:28006"
  }
  ```

---

### 2.2. A2A 전자공시 분석 요청 (`POST /`)
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
        "content": "종목코드 005930의 최근 3개월 주요 공시 내역 및 호악재 영향도 분석 요청"
      }
    },
    "id": "req-dart-001"
  }
  ```
- **Response Payload 예시**:
  ```json
  {
    "jsonrpc": "2.0",
    "result": {
      "event": {
        "author": "dart_disclosure_agent",
        "content": {
          "role": "model",
          "parts": [
            {
              "text": "📑 [삼성전자: 005930] 전자공시 이벤트 분석 보고서\n- 종합 영향도: POSITIVE (우호적)\n- 주요 공시 1: 10조 원 규모 자사주 매입 및 소각 결정 (주주가치 제고, POSITIVE_HIGH)\n- 주요 공시 2: 시설투자(HBM 전용 생산라인 증설) 5조 원 투자 공시\n- 오버행 리스크: CB/BW 미상환 잔액 없음 (오버행 위험도 0점)"
            }
          ]
        }
      }
    },
    "id": "req-dart-001"
  }
  ```

---

### 2.3. Prometheus 메트릭 수집 (`GET /metrics`)
- **Method**: `GET`
- **Path**: `/metrics`
- **Response**: OpenMetrics / Prometheus 포맷

---

### 2.4. Health Check (`GET /health`)
- **Method**: `GET`
- **Path**: `/health`
- **Response**: `{"status": "ok"}`
