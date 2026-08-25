# 🤖 Orchestrator Server (`app`) 문서

본 문서는 **Agent Ecosystem의 중앙 컨트롤러 서버인 `app` (Orchestrator Server)**의 아키텍처, 디렉토리 구조, REST API 엔드포인트 및 테스트 방법을 설명합니다.

---

## 1. 개요

`app` 모듈은 사용자 및 클라이언트 요청을 수신하는 단일 진입점(Entrypoint)입니다. 내부적으로 **`SupervisorAgent`**가 요청을 해석하고, **MCP Server**를 통해 탐색된 원격 서브 에이전트(Remote Sub-Agents)들에게 작업을 적절히 위임한 후 최종 결과를 종합하여 응답합니다.

---

## 2. 디렉토리 및 파일 구조

```text
app/
├── agents/                 # Domain Agent 로직
│   ├── base.py             # BaseAgent 추상 인터페이스 (abc.ABC)
│   ├── supervisor.py       # SupervisorAgent (MCP 연동 및 Task 위임)
│   ├── factory.py          # AgentFactory (SupervisorAgent 조립 팩토리)
│   └── prompts/            # Supervisor 시스템 프롬프트 (supervisor.yml)
├── api/                    # REST API 컨트롤러
│   ├── v1/                 # API Version 1 Router
│   │   ├── orchestrator/   # /api/v1/supervisor/invoke 등 오케스트레이터 컨트롤러
│   │   │   ├── router.py   # HTTP Endpoints (invoke, stream, info)
│   │   │   ├── schema.py   # Pydantic Request/Response DTO Schemas
│   │   │   └── service.py  # 비즈니스 오케스트레이션 서비스
│   │   └── router.py       # v1 통합 라우터
│   ├── health.py           # GET /health Check 라우터
│   └── router.py           # 루트 라우터
├── core/                   # 인프라스트럭처 및 환경설정
│   ├── config.py           # Pydantic BaseSettings 기반 앱 설정 (Settings)
│   ├── lifespan.py         # FastAPI Startup/Shutdown 이벤트 라이프사이클
│   ├── llm.py              # Multi-provider LLM Singleton Registry
│   └── mcp_client.py       # MCP Server SSE 연동 및 Agent Card 동적 수집 유틸
├── dependencies/           # FastAPI 의존성 주입 (Dependency Injection)
│   ├── supervisor.py       # get_supervisor 의존성 주입 함수
│   └── llm.py              # get_llm 의존성 주입 함수
├── tests/                  # Pytest 유닛 및 통합 테스트 수트
│   ├── test_health.py      # Health API 테스트
│   ├── test_supervisor.py  # Supervisor 에이전트 동작 테스트
│   └── test_factory.py     # AgentFactory 생성 테스트
├── application.py          # FastAPI 앱 생성 팩토리 (create_app)
├── main.py                 # Uvicorn 진입점 (Port: 28000)
├── Dockerfile              # Docker 이미지 빌드 파일
├── docker-compose.yml      # 도커 컴포즈 실행 스펙
├── pyproject.toml          # uv 및 패키지 메타데이터
└── pyrightconfig.json      # Python 정적 타입 검사 설정
```

---

## 3. 핵심 레이어 아키텍처

1. **Domain Agent Layer (`agents/`)**:
   - `BaseAgent`: 추상 기본 클래스로 `invoke()` 및 `stream()` 비동기 인터페이스 정의.
   - `SupervisorAgent`: MCP Server에서 등록된 서브 에이전트 도구를 동적 구성하고 LangChain/LangGraph 에이전트로 태스크 처리.
   - `AgentFactory`: 설정을 바탕으로 LLM 레지스트리 및 MCP 클라이언트를 결합하여 SupervisorAgent 인스턴스를 동적으로 생성.
2. **Controller Layer (`api/`)**:
   - FastAPI 라우터 모듈로 요청 데이터를 validation하고 서비스 레이어로 전달.
3. **Core Layer (`core/`)**:
   - `Settings`: `.env` 파일을 로드하고 `Pydantic BaseSettings`로 검증.
   - `LLMRegistry`: OpenAI, Anthropic, Google API 키 존재 유무에 따라 사용할 LLM을 자동 초기화 및 제공.
   - `mcp_client`: FastMCP SSE 서버에 연결하여 에이전트 카드를 파싱하고 도구 객체로 변환.

---

## 4. API 엔드포인트 명세

### 4.1. Supervisor 태스크 수행 (`POST /api/v1/supervisor/invoke`)
- **설명**: 단건 비동기 요청을 처리하고 원격 에이전트를 동적으로 호출하여 종합 결과를 반환합니다.
- **Request Body**:
  ```json
  {
    "message": "echo 에이전트에게 인사하고, 서울 날씨 알아봐줘",
    "thread_id": "optional_session_123"
  }
  ```
- **Response Body**:
  ```json
  {
    "result": "Echo 에이전트 응답: ... 서울의 현재 날씨는 맑음(22°C)입니다.",
    "thread_id": "optional_session_123"
  }
  ```

### 4.2. Supervisor 스트리밍 응답 (`POST /api/v1/supervisor/stream`)
- **설명**: Server-Sent Events (SSE) 토큰 스트리밍으로 결과를 실시간 전송합니다.

### 4.3. Supervisor 정보 조회 (`GET /api/v1/supervisor/info`)
- **설명**: 현재 등록된 Supervisor 에이전트 이름 및 동적 발견된 Remote Sub-Agent 목록을 반환합니다.

### 4.4. 헬스 체크 (`GET /health`)
- **설명**: 컨테이너의 상태 및 헬스 체크 응답 (`{"status": "ok"}`).

---

## 5. 실행 및 테스트 (Execution & Testing)

### 5.1. 독립 개발 서버 실행
```bash
cd app
uv run python main.py
```

### 5.2. Pytest 유닛 테스트 실행
```bash
cd app
uv run pytest
```
