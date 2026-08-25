from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class BaseAgent(ABC):
    """모든 agent가 구현해야 하는 공통 인터페이스 — FastAPI 의존 없음"""

    def __init__(self):
        self._name = self.__class__.__name__

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    async def ainvoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """비동기 실행 — LangGraph / LangChain ainvoke 호환"""
        ...

    @abstractmethod
    def astream(self, inputs: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """비동기 스트리밍 — SSE / A2A Phase 에서 사용"""
        ...
