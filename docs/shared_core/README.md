# 📦 Shared Core Library (`shared_core`) 문서

본 문서는 **전체 Agent Ecosystem 프로젝트에서 공통으로 참조 및 재사용하는 라이브러리 모듈 `shared_core`**에 대한 기술 명세서입니다.

---

## 1. 개요

`shared_core`는 독립된 Python 패키지로 구동되며 `app`, `agent_server`, `mcp_server` 등 모든 마이크로서비스에서 **일관된 구조화 로깅**, **YAML 프롬프트 안전 로드**, 그리고 **LangGraph 파이프라인 노드 추상화(`BaseNode`)**를 제공합니다.

---

## 2. 디렉토리 및 패키지 구조

```text
shared_core/
├── src/shared_core/
│   ├── __init__.py         # 패키지 익스포트 인터페이스 (logger, load_prompt, BaseNode)
│   ├── base_node.py        # ⚡ LangGraph 노드 추상화 객체 (ABC, 로깅 & DI 관리)
│   ├── logger.py           # Structlog 기반 UTF-8 구조화 로그 로거
│   ├── prompt.py           # YAML 프롬프트 로더 유틸리티
│   └── py.typed            # PEP 561 Type Hinting 마커 파일
├── pyproject.toml          # uv 및 패키지 빌드 스펙
├── uv.lock                 # 의존성 잠금 파일
└── README.md               # 메인 참조 링커
```

---

## 3. 핵심 모듈 상세

### 3.1. `base_node.py` (LangGraph 노드 추상화 기본 클래스 `BaseNode`)

Python 표준 `abc.ABC`를 기반으로 정의된 파이프라인 노드 추상화 객체입니다. LangGraph StateGraph 노드 개발 시 표준화된 비즈니스 로직 구현, 자동 로깅, 실행 시간 측정 및 의존성 주입(Dependency Injection)을 일원화하여 관리합니다.

#### 주요 기능
1. **`@abstractmethod async def process(self, state: StateType) -> ReturnType`**:
   - 하위 노드 클래스에서 핵심 비즈니스 로직 구현을 강제.
2. **자동 로깅 및 메트릭 트래킹 (`structlog`)**:
   - `__call__` 실행 시 `task.<node_name>.started` (입력 키 정보)
   - 정상 완료 시 `task.<node_name>.completed` (소요 시간 `duration_ms`, 결과 키 정보)
   - 예외 발생 시 `task.<node_name>.failed` (에러 타입, 메시지, Traceback) 자동 기록.
3. **의존성 주입 & 관리 (Dependency Injection)**:
   - 노드 초기화 시 `**dependencies` (DB 세션, LLM 모델, 캐시 클라이언트 등)를 주입받아 보관.
   - `get_dependency(key)`, `set_dependency(key, value)` 메서드 지원.
4. **라이프사이클 훅 (Lifecycle Hooks)**:
   - `before_process(state)`, `after_process(state, result)`, `on_error(state, error)`를 오버라이드하여 전/후처리 확장 가능.
5. **LangGraph 호환성**:
   - `async def __call__(self, state)` 구현으로 `graph.add_node("name", node_instance)` 형태로 즉시 바인딩 가능.

#### 💡 사용 예시 (LangGraph 노드 구현)

```python
from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, START, END
from shared_core import BaseNode

# 1. State 정의
class StockState(TypedDict):
    ticker: str
    price: float
    analysis: str

# 2. BaseNode를 상속받은 커스텀 노드 구현
class StockAnalysisNode(BaseNode[StockState, Dict[str, Any]]):
    async def process(self, state: StockState) -> Dict[str, Any]:
        # 주입된 의존성 조회
        db_client = self.get_dependency("db")
        llm = self.get_dependency("llm")
        
        ticker = state["ticker"]
        # 비즈니스 로직 수행
        return {
            "price": 75000.0,
            "analysis": f"[{ticker}] 펀더멘털 및 기술적 분석 완료 (DB: {db_client})"
        }

# 3. 노드 인스턴스화 (의존성 주입)
analysis_node = StockAnalysisNode(
    name="stock_analyzer",
    db="postgres_session_factory",
    llm="gemini-2.5-flash"
)

# 4. LangGraph에 노드로 등록
workflow = StateGraph(StockState)
workflow.add_node("analyze", analysis_node)  # __call__이 자동 실행됨
workflow.add_edge(START, "analyze")
workflow.add_edge("analyze", END)

app = workflow.compile()
```

---

### 3.2. `logger.py` (구조화 로깅 유틸리티)
- **주요 기능**: `structlog` 라이브러리를 바인딩하여 한국어/UTF-8 문자가 깨지지 않도록 처리하고 JSON 또는 Console 색상 출력을 지원합니다.
- **주요 함수**:
  - `setup_logger(log_level="INFO", app_name="app")`: 전역 로거 포맷터 및 핸들러 초기화.
  - `logger`: 인스턴스화된 `structlog` 로거 객체.
- **로그 네이밍 컨벤션**:
  - `task.<node_name>.<event>`: 태스크 처리 단계 로그 (예: `task.stock_analyzer.started`, `task.stock_analyzer.completed`)
  - `artifact.<module>.<event>`: 아티팩트 및 메시지 생성 로그 (예: `artifact.data_processing_agent.event_created`)

---

### 3.3. `prompt.py` (YAML 프롬프트 로더)
- **주요 기능**: 지정된 YAML 프롬프트 파일 경로에서 특정 키의 텍스트 값을 안전하게 파싱하여 로드합니다.
- **주요 함수**:
  - `load_prompt(yaml_path: str | Path, key: str = "system_prompt", default: str = "") -> str`
- **예시 사용법**:
  ```python
  from shared_core.prompt import load_prompt

  prompt_text = load_prompt("prompts/data_processing.yml", key="data_processing_template")
  ```
