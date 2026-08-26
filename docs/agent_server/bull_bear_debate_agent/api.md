# 🔌 Bull vs Bear Debate Sub-Agent API 명세서

Bull vs Bear Debate Sub-Agent (`agent_bull_bear_debate_server`)가 제공하는 HTTP 및 A2A JSON-RPC 2.0 엔드포인트 명세입니다.
본 서비스는 Google ADK의 `to_a2a(bull_bear_debate_agent)` 변환 함수를 통해 생성된 Starlette/FastAPI 애플리케이션으로 동작합니다.

---

## 1. 기본 정보 (Base Information)

- **Base URL**: `http://agent_bull_bear_debate_server:28008` (또는 `http://localhost:28008`)
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
    "name": "bull_bear_debate_agent",
    "description": "상승론(Bull)과 하락론(Bear) 대립 토론 기반 객관적 투자 판단 및 의사결정 에이전트",
    "url": "http://agent_bull_bear_debate_server:28008"
  }
  ```

---

### 2.2. A2A 토론 및 최종 투자 판단 요청 (`POST /`)
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
        "content": "종목코드 005930(삼성전자)에 대한 종합 분석 데이터를 바탕으로 Bull vs Bear 토론 및 최종 투자 의견 도출 요청"
      }
    },
    "id": "req-debate-001"
  }
  ```
- **Response Payload 예시**:
  ```json
  {
    "jsonrpc": "2.0",
    "result": {
      "event": {
        "author": "bull_bear_debate_agent",
        "content": {
          "role": "model",
          "parts": [
            {
              "text": "⚖️ [삼성전자: 005930] Bull vs Bear 심의 및 최종 투자 의견서\n\n1. 🐂 Bull의 주장 (점수: 85점):\n- HBM3E 공급 본격화에 따른 영업이익 서프라이즈 가시화\n- 밸류에이션(PBR 1.25배) 역사적 하단 구간\n\n2. 🐻 Bear의 주장 (점수: 62점):\n- 레거시 D램 가격 상승세 둔화 우려 및 글로벌 경기 침체 리스크\n- 외국인 단기 차익 실현 가능성\n\n3. ⚖️ 판사(Judge) 최종 결정:\n- 최종 투자 의견: BUY (매수)\n- 모델 확신도: 78%\n- 적정 목표가: 88,000원 (+17.3%)\n- 추천 손절가: 71,500원 (-4.6%)"
            }
          ]
        }
      }
    },
    "id": "req-debate-001"
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
