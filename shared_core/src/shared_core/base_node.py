from abc import ABC, abstractmethod
import time
from typing import Any, Dict, Generic, Optional, TypeVar
import structlog
from .logger import logger as default_logger

StateType = TypeVar("StateType", bound=Dict[str, Any])
ReturnType = TypeVar("ReturnType", bound=Dict[str, Any])

class BaseNode(ABC, Generic[StateType, ReturnType]):
    """
    LangGraph 및 파이프라인에서 사용하는 노드의 추상화 기본 클래스.
    
    주요 기능:
    1. 추상 메서드 `process()`를 통한 표준화된 노드 비즈니스 로직 구현 강제.
    2. 노드 실행 시작, 완료, 소요 시간(ms), 에러에 대한 구조화 로깅(structlog) 자동화.
    3. LLM, DB 세션, API 클라이언트 등 외부 의존성(Dependency Injection) 관리.
    4. 전/후처리 훅(before_process, after_process, on_error)을 통한 확장성 제공.
    5. LangGraph StateGraph의 노드로 즉시 등록 가능한 비동기 Callable (`__call__`) 인터페이스.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        logger: Optional[structlog.stdlib.BoundLogger] = None,
        **dependencies: Any
    ):
        """
        BaseNode 초기화.

        Args:
            name: 노드의 고유 식별 이름 (미지정 시 클래스명 사용)
            logger: 커스텀 structlog 로거 인스턴스 (미지정 시 기본 로거에 node 이름 바인딩)
            **dependencies: DB 커넥션, LLM, 캐시 클라이언트 등 노드에 주입할 의존성 객체들
        """
        self.name = name or self.__class__.__name__
        self._dependencies: Dict[str, Any] = dict(dependencies)
        
        base_log = logger or default_logger
        self.logger = base_log.bind(node=self.name)

    @property
    def dependencies(self) -> Dict[str, Any]:
        """주입된 의존성 딕셔너리 반환"""
        return self._dependencies

    def get_dependency(self, key: str, default: Any = None) -> Any:
        """특정 의존성 객체 조회"""
        return self._dependencies.get(key, default)

    def set_dependency(self, key: str, value: Any) -> None:
        """의존성 객체 동적 추가/수정"""
        self._dependencies[key] = value

    async def before_process(self, state: StateType) -> None:
        """노드 실행 전 호출되는 훅 (필요 시 하위 클래스에서 오버라이드)"""
        pass

    async def after_process(self, state: StateType, result: ReturnType) -> None:
        """노드 실행 성공 후 호출되는 훅 (필요 시 하위 클래스에서 오버라이드)"""
        pass

    async def on_error(self, state: StateType, error: Exception) -> None:
        """노드 실행 중 예외 발생 시 호출되는 훅 (필요 시 하위 클래스에서 오버라이드)"""
        pass

    @abstractmethod
    async def process(self, state: StateType) -> ReturnType:
        """
        하위 노드 클래스에서 반드시 구현해야 하는 핵심 비즈니스 로직.

        Args:
            state: LangGraph 파이프라인의 현재 상태 (State)

        Returns:
            갱신할 상태 딕셔너리 (State updates)
        """
        raise NotImplementedError("Subclasses must implement process()")

    async def __call__(self, state: StateType) -> ReturnType:
        """
        LangGraph 노드 엔트리포인트.
        로깅, 실행 시간 측정, 라이프사이클 훅 및 에러 핸들링을 자동 수행합니다.
        """
        start_time = time.perf_counter()
        state_keys = list(state.keys()) if isinstance(state, dict) else []

        self.logger.info(
            f"task.{self.name}.started",
            input_keys=state_keys,
            dependency_keys=list(self._dependencies.keys())
        )

        try:
            # 1. 실행 전 훅
            await self.before_process(state)

            # 2. 메인 비즈니스 로직 실행
            result = await self.process(state)

            # 3. 실행 후 훅
            await self.after_process(state, result)

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            result_keys = list(result.keys()) if isinstance(result, dict) else []

            self.logger.info(
                f"task.{self.name}.completed",
                duration_ms=duration_ms,
                result_keys=result_keys
            )
            return result

        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.logger.error(
                f"task.{self.name}.failed",
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=duration_ms,
                exc_info=True
            )
            # 4. 에러 훅
            await self.on_error(state, e)
            raise e
