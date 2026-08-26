# 🔌 Fundamental Analysis Sub-Agent API 명세서

Fundamental Analysis Sub-Agent (`agent_fundamental_server`)가 제공하는 HTTP 및 A2A JSON-RPC 2.0 엔드포인트 명세입니다.
본 서비스는 Google ADK의 `to_a2a(fundamental_agent)` 변환 함수를 통해 생성된 Starlette/FastAPI 애플리케이션으로 동작합니다.

---

## 1. 기본 정보 (Base Information)

- **Base URL**: `http://agent_fundamental_server:28004` (또는 `http://localhost:28004`)
- **A2A Adapter**: `google.adk.a2a.utils.agent_to_a2a.to_a2a`
- **Protocol**: HTTP / Google ADK A2A JSON-RPC 2.0
- **Content-Type**: `application/json`

---

## 2. 엔드포인트 목록 (Endpoints)

### 2.1. Agent Card 조회 (`GET /.well-known/agent-card.json`)
- **설명**: `to_a2a(agent)`에 의해 자동 서빙되는 에이전트 메타데이터 카드입니다.
- **Method**: `GET`
- **Path**: `/.well-known/agent-card.json`
- **Response 예시 (`200 OK`)**:
  ```json
  {
    "name": "fundamental_agent",
    "description": "재무제표, 밸류에이션 지표 및 실적 펀더멘털 분석 에이전트",
    "url": "http://agent_fundamental_server:28004"
  }
  ```

---

### 2.2. A2A 펀더멘털 분석 요청 (`POST /`)
- **설명**: 종목 코드 및 기간을 입력받아 3개년 재무제표 및 밸류에이션(PER/PBR/ROE) 분석 결과를 반환합니다.
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
        "content": "종목코드 005930의 최근 3개년 재무제표 건전성 및 밸류에이션 분석 요청"
      }
    },
    "id": "req-fund-001"
  }
  ```
- **Response Payload 예시**:
  ```json
  {
    "jsonrpc": "2.0",
    "result": {
      "event": {
        "author": "fundamental_agent",
        "content": {
          "role": "model",
          "parts": [
            {
              "text": "📊 [삼성전자: 005930] 펀더멘털 분석 보고서\n- 재무 건전성 등급: A+ (부채비율 26.4%, 유동비율 245%)\n- 밸류에이션: PER 13.8배 (업종 평균 16.2배 대비 저평가), PBR 1.25배, ROE 9.8%\n- 영업이익 추이: 전년 동기 대비 +24.3% 성장\n- FCF(잉여현금흐름): 18.4조 원 (안정적 현금창출능력)"
            }
          ]
        }
      }
    },
    "id": "req-fund-001"
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
