# 🔌 Risk Management Sub-Agent API 명세서

Risk Management Sub-Agent (`agent_risk_management_server`)가 제공하는 HTTP 및 A2A JSON-RPC 2.0 엔드포인트 명세입니다.
본 서비스는 **100% Rule-Based(결정론적 수식 및 포트폴리오 비중 한도 규칙)**로 동작하는 리스크 게이트키퍼 검증 엔진입니다.

---

## 1. 기본 정보 (Base Information)

- **Base URL**: `http://agent_risk_management_server:28009` (또는 `http://localhost:28009`)
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
    "name": "risk_management_agent",
    "description": "100% Rule-Based 포트폴리오 비중 한도, 변동성 손절선 및 급락장 게이트키퍼 리스크 검증 에이전트",
    "url": "http://agent_risk_management_server:28009"
  }
  ```

---

### 2.2. A2A Rule-Based 리스크 심의 및 승인 요청 (`POST /`)
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
        "content": "삼성전자(005930) 신규 매수 제안 비중 15%에 대한 Rule-based 리스크 심의 요청"
      }
    },
    "id": "req-risk-001"
  }
  ```
- **Response Payload 예시**:
  ```json
  {
    "jsonrpc": "2.0",
    "result": {
      "event": {
        "author": "risk_management_agent",
        "content": {
          "role": "model",
          "parts": [
            {
              "text": "🛡️ [Rule-Based 리스크 심의 결과]\n- 판정 결과: ADJUSTED (수량 축소 조건부 승인)\n- 검증 룰 1 (시장 패닉): 통과 (코스피 당일 등락률 -0.42%로 -3% 기준 미달)\n- 검증 룰 2 (종목 한도): 통과 (제안 비중 15% <= 단일 종목 최대 한도 15%)\n- 검증 룰 3 (섹터 한도): 위반 ➡️ 조정 (반도체 섹터 기존 22% + 15% = 37% > 한도 30%)\n- 최종 승인 비중: 8.0% (초기 제안 15% ➡️ 8%로 축소 승인)\n- 필수 손절가: 71,800원 (현재가 75,000원 대비 ATR 1.5배 기준)\n- 검증 방식: 100% Deterministic Rule Engine (No Hallucination)"
            }
          ]
        }
      }
    },
    "id": "req-risk-001"
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
