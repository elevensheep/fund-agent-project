# 📝 LangGraph Technical Reference Guide

본 문서는 프로젝트에서 사용하는 **LangGraph 패키지 버전 스펙 및 API Signature 레퍼런스** 정리 문서입니다. (`langgraph_info.txt` 및 `signature.txt` 기반)

---

## 1. LangGraph Package Specification

| 항목 | 정보 |
| :--- | :--- |
| **Package Name** | `langgraph` |
| **Installed Version** | `1.2.11` |
| **Python Environment** | `/opt/venv/lib/python3.12/site-packages` |
| **Dependencies** | `langchain-core`, `langgraph-checkpoint`, `langgraph-prebuilt`, `langgraph-sdk`, `pydantic`, `xxhash` |
| **Required-by Modules** | `a2a-server`, `langchain` |

---

## 2. ReAct Agent State Graph Signature (`create_react_agent`)

LangGraph의 `create_react_agent` 메인 빌더 메서드의 타입 시그니처 레퍼런스입니다.

```python
create_react_agent(
    model: BaseChatModel | Runnable | Callable,
    tools: Sequence[BaseTool | Callable | dict] | ToolNode,
    *,
    prompt: SystemMessage | str | Callable | Runnable | None = None,
    response_format: dict | type[BaseModel] | tuple | None = None,
    pre_model_hook: Runnable | Callable | None = None,
    post_model_hook: Runnable | Callable | None = None,
    state_schema: type[StateSchema] | None = None,
    context_schema: type[Any] | None = None,
    checkpointer: None | bool | BaseCheckpointSaver = None,
    store: BaseStore | None = None,
    interrupt_before: list[str] | None = None,
    interrupt_after: list[str] | None = None,
    debug: bool = False,
    version: Literal['v1', 'v2'] = 'v2',
    name: str | None = None,
    **deprecated_kwargs: Any
) -> CompiledStateGraph
```

### 주요 파라미터 노트
- `model`: 에이전트 실행에 사용될 LLM 모델 (`BaseChatModel` 또는 `Runnable`).
- `tools`: 에이전트가 호출 가능한 도구 바인딩 목록.
- `prompt`: 시스템 프롬프트 (`SystemMessage` 객체 또는 문자열).
- `checkpointer`: 세션 대화 상태 저장을 위한 체크포인터 인스턴스.
- `version`: 그래프 컴파일 버전 (`v2` 기본 적용).
