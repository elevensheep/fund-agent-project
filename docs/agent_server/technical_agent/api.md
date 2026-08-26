# 🔌 Technical Analysis Sub-Agent API 명세서

Technical Analysis Sub-Agent (`agent_technical_server`)가 제공하는 HTTP 및 A2A JSON-RPC 2.0 엔드포인트 명세입니다.
본 서비스는 Google ADK의 `to_a2a(technical_agent)` 변환 함수를 통해 생성된 Starlette/FastAPI 애플리케이션으로 동작합니다.

---

## 1. 기본 정보 (Base Information)

- **Base URL**: `http://agent_technical_server:28005` (또는 `http://localhost:28005`)
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
    "name": "technical_agent",
    "description": "차트 패턴, 보조 지표 및 수급 기반 기술적 매매 시그널 분석 에이전트",
    "url": "http://agent_technical_server:28005"
  }
  ```

---

### 2.2. A2A 기술적 차트 분석 요청 (`POST /`)
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
        "content": "종목코드 005930의 일봉 기술적 지표 및 지지/저항선 분석 요청"
      }
    },
    "id": "req-tech-001"
  }
  ```
- **Response Payload 예시**:
  ```json
  {
    "jsonrpc": "2.0",
    "result": {
      "event": {
        "author": "technical_agent",
        "content": {
          "role": "model",
          "parts": [
            {
              "text": "📈 [삼성전자: 005930] 기술적 차트 분석 보고서\n- 매매 시그널: BUY (매수 우위)\n- 핵심 지표: RSI 58.4 (중립-상승), MACD 히스토그램 양전환, 20일 이평선 지지 확인\n- 수급 동향: 외국인 3일 연속 순매수 (+4,200억 원)\n- 주요 가격대: 1차 지지선 73,800원 / 1차 저항선 78,500원"
            }
          ]
        }
      }
    },
    "id": "req-tech-001"
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
