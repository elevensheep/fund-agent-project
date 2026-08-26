# 🤖 Orchestrator Server (`app`) 문서

본 문서는 **Agent Ecosystem의 중앙 컨트롤러 서버인 `app` (Orchestrator Server)**의 Plan-and-Execute 아키텍처, 디렉토리 구조, REST API 엔드포인트 및 테스트 방법을 설명합니다.

---

## 1. 개요 & Plan-and-Execute 아키텍처 채택 배경

`app` 모듈은 사용자 및 클라이언트 요청을 수신하는 단일 진입점(Entrypoint)입니다.
8대의 전문 서브 에이전트(Sub-Agents)를 효율적으로 조율하기 위해, 단일 ReAct 루프의 지연시간(Latency)과 경로 이탈(Goal Drift) 문제를 해결한 **Plan-and-Execute (Planner ➡️ Parallel Dispatcher ➡️ Synthesizer)** 패턴을 채택하고 있습니다.

> [!TIP]
> **왜 Plan-and-Execute 구조인가?**
> 1. **병렬 실행(Parallelism)을 통한 응답 속도 3~5배 단축**: 펀더멘털, 차트, 공시, 매크로 분석 등 서로 독립적인 태스크를 `asyncio.gather()`로 동시 실행하여 응답 지연을 획기적으로 줄입니다.
> 2. **사용자 요청 맞춤형 동적 라우팅 (비용 절감)**: 단순 뉴스 질의 시에는 `web_search_agent`만 호출하고, 종합 분석 시에만 4단계 전체 파이프라인을 실행합니다.
> 3. **명확한 실행 추적성(Observability)**: 초기에 수립된 `ExecutionPlan`에 따라 단계별 실행 로그가 기록되어 디버깅과 모니터링이 용이합니다.

---

## 2. 디렉토리 및 파일 구조

```text
app/
├── agents/                 # Domain Agent 및 Plan-and-Execute 오케스트레이션 로직
│   ├── base.py             # BaseAgent 추상 인터페이스 (abc.ABC)
│   ├── supervisor.py       # SupervisorAgent (Plan-and-Execute 메인 워크플로우)
│   ├── planner.py          # ⚡ [Planner] 사용자 요청 의도 분석 & 실행 계획(DAG) 수립
│   ├── dispatcher.py       # ⚡ [Dispatcher] A2A 서브 에이전트 비동기 병렬 호출기 (asyncio.gather)
│   ├── synthesizer.py      # ⚡ [Synthesizer] 수집/분석 결과 종합 및 최종 리포트 작성
│   ├── factory.py          # AgentFactory (SupervisorAgent 조립 팩토리)
│   └── prompts/            # YAML 프롬프트 템플릿
│       ├── supervisor.yml  # Supervisor 시스템 프롬프트
│       ├── planner.yml     # Planner 전용 프롬프트
│       └── synthesizer.yml # 리포트 생성 프롬프트
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
│   ├── test_planner.py     # Planner 실행 계획 생성 테스트
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

## 3. Plan-and-Execute 워크플로우 구조

```mermaid
graph TD
    User["👤 사용자 요청<br/>'삼성전자(005930) 종합 분석 및 투자 심의해줘'"] --> Planner["1. 📋 Planner Agent (계획 수립)<br/>- 사용자 의도 분석<br/>- 필요 서브 에이전트 선별 및 Step별 실행 계획(DAG) 수립"]

    Planner -->|ExecutionPlan (Step 1~4)| Dispatcher["2. ⚡ Parallel Dispatcher (병렬 디스패처)"]

    subgraph Step 1. 병렬 수집 레이어 (동시 호출)
        Dispatcher -->|A2A 호출| WS["🔍 web_search_agent (28003)"]
        Dispatcher -->|A2A 호출| DP["📊 data_processing_agent (28001)"]
    end

    subgraph Step 2. 병렬 심층 분석 레이어 (동시 호출)
        WS & DP --> FA["📈 fundamental_agent (28004)"]
        WS & DP --> TA["📉 technical_agent (28005)"]
        WS & DP --> DART["📑 dart_disclosure_agent (28006)"]
        WS & DP --> Macro["🌐 macro_sector_agent (28007)"]
    end

    subgraph Step 3. 토론 및 최종 판단
        FA & TA & DART & Macro --> BB["🐂🐻 bull_bear_debate_agent (28008)"]
    end

    subgraph Step 4. 리스크 검증 (100% Rule-Based)
        BB --> Risk["🛡️ risk_management_agent (28009)"]
    end

    Risk --> Synthesizer["3. 📝 Synthesizer Agent (종합 리포트 생성)"]
    Synthesizer --> FinalResp["👤 최종 사용자 응답"]
```

---

## 4. 핵심 컴포넌트 구현 명세

### 4.1. `planner.py` (실행 계획 수립)

사용자 질문을 분석하여 실행할 서브 에이전트 목록과 의존 관계(단계별 그룹)를 Pydantic 구조체로 생성합니다.

```python
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class PlanStep(BaseModel):
    step_id: int = Field(description="실행 단계 번호 (동일 번호는 병렬 실행)")
    agent_name: str = Field(description="호출할 서브 에이전트 명 (e.g. web_search_agent)")
    task_prompt: str = Field(description="서브 에이전트에 전달할 세부 지시문")

class ExecutionPlan(BaseModel):
    ticker: str = Field(description="대상 주식 종목 코드 (e.g. 005930)")
    query_intent: str = Field(description="사용자 질의 의도: NEWS_ONLY, CHART_ONLY, FULL_ANALYSIS 등")
    steps: List[PlanStep] = Field(description="실행할 단계별 서브 에이전트 목록")
```

### 4.2. `dispatcher.py` (비동기 병렬 호출기)

`mcp_client`가 동적 탐색한 Agent Card의 URL을 참조하여, 동일한 `step_id`를 가진 서브 에이전트들을 `asyncio.gather()`로 병렬 실행합니다.

```python
import asyncio
import httpx
from typing import Dict, Any, List

class ParallelDispatcher:
    def __init__(self, agent_cards: Dict[str, str]):
        self.agent_cards = agent_cards  # {agent_name: url}

    async def execute_step_parallel(self, steps: List[PlanStep]) -> List[Dict[str, Any]]:
        """동일 단계의 서브 에이전트들을 비동기 병렬 호출 (A2A JSON-RPC 2.0)"""
        tasks = [self._call_agent(step) for step in steps]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _call_agent(self, step: PlanStep) -> Dict[str, Any]:
        url = self.agent_cards.get(step.agent_name)
        payload = {
            "jsonrpc": "2.0",
            "method": "SendMessage",
            "params": {"message": {"role": "user", "content": step.task_prompt}},
            "id": f"dispatch-{step.agent_name}"
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            return resp.json()["result"]["event"]
```

---

## 5. API 엔드포인트 명세

### 5.1. Supervisor 태스크 수행 (`POST /api/v1/supervisor/invoke`)
- **설명**: 단건 비동기 요청을 수신하여 `Planner` ➡️ `Parallel Dispatcher` ➡️ `Synthesizer` 파이프라인을 실행하고 종합 리포트를 반환합니다.
- **Request Body**:
  ```json
  {
    "message": "삼성전자(005930)의 최신 뉴스 및 재무/차트 분석을 수행하고 리스크 심의를 거쳐 투자 의견을 제시해줘",
    "thread_id": "session_stock_001"
  }
  ```
- **Response Body**:
  ```json
  {
    "result": "📊 [삼성전자(005930) 종합 투자 심의 리포트]\n1. 펀더멘털: PER 11.2배로 밸류에이션 매력 높음\n2. 기술적 분석: 20일 이평선(74,200원) 상향 돌파 시도\n3. 토론 결과: 판사 최종 의견 BUY (확신도 82%)\n4. 리스크 심의: ADJUSTED 승인 (포트폴리오 비중 8%, 손절가 71,800원 확정)",
    "thread_id": "session_stock_001"
  }
  ```

### 5.2. Supervisor 스트리밍 응답 (`POST /api/v1/supervisor/stream`)
- **설명**: Server-Sent Events (SSE) 토큰 스트리밍으로 결과를 실시간 전송합니다.

### 5.3. Supervisor 정보 조회 (`GET /api/v1/supervisor/info`)
- **설명**: 현재 등록된 Supervisor 에이전트 이름 및 동적 발견된 8대 Remote Sub-Agent 목록을 반환합니다.

### 5.4. 헬스 체크 (`GET /health`)
- **설명**: 컨테이너의 상태 및 헬스 체크 응답 (`{"status": "ok"}`).

---

## 6. 실행 및 테스트 (Execution & Testing)

### 6.1. 독립 개발 서버 실행
```bash
cd app
uv run python main.py
```

### 6.2. Pytest 유닛 및 Planner 테스트 실행
```bash
cd app
uv run pytest
```
