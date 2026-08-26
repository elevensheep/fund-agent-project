# 🔌 Macroeconomic & Sector Sub-Agent API 명세서

Macroeconomic & Sector Sub-Agent (`agent_macro_sector_server`)가 제공하는 HTTP 및 A2A JSON-RPC 2.0 엔드포인트 명세입니다.
본 서비스는 Google ADK의 `to_a2a(macro_sector_agent)` 변환 함수를 통해 생성된 Starlette/FastAPI 애플리케이션으로 동작합니다.

---

## 1. 기본 정보 (Base Information)

- **Base URL**: `http://agent_macro_sector_server:28007` (또는 `http://localhost:28007`)
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
    "name": "macro_sector_agent",
    "description": "금리, 환율, 글로벌 증시 및 산업 섹터 트렌드 분석 에이전트",
    "url": "http://agent_macro_sector_server:28007"
  }
  ```

---

### 2.2. A2A 거시경제 및 섹터 분석 요청 (`POST /`)
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
        "content": "반도체 섹터 및 삼성전자(005930)에 영향을 주는 글로벌 매크로 환경 분석 요청"
      }
    },
    "id": "req-macro-001"
  }
  ```
- **Response Payload 예시**:
  ```json
  {
    "jsonrpc": "2.0",
    "result": {
      "event": {
        "author": "macro_sector_agent",
        "content": {
          "role": "model",
          "parts": [
            {
              "text": "🌐 [반도체 섹터 / 매크로 환경 분석 보고서]\n- 매크로 우호도 점수: 78점 (FAVORABLE - 우호적)\n- 환율/금리: USD/KRW 1,340원 (수출 우호적), 미 국채 10년물 금리 안정세 (4.12%)\n- 글로벌 섹터: 필라델피아 반도체 지수(SOX) +2.8% 상승 마감, AI 서버 수요 견조\n- 섹터 수급: 최근 3일간 국내 증시에서 반도체 업종으로 외국인 자금 집중 유입 (+1.2조 원)"
            }
          ]
        }
      }
    },
    "id": "req-macro-001"
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
