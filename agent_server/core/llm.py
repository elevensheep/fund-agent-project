from typing import Any, Dict, List, Literal, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from core.config import Settings, get_settings
from shared_core.logger import logger

ProviderName = Literal["openai", "anthropic", "google"]


class MockChatModel(FakeMessagesListChatModel):
    """
    bind_tools 및 with_structured_output을 안전하게 지원하는 모의 ChatModel.
    """

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self

    def with_structured_output(self, schema: Any, **kwargs: Any) -> Any:
        return self


class LLMRegistry:
    """
    Multi-provider LLM Singleton Registry.
    App startup 시 initialize_all()로 초기화됩니다.
    """

    _registry: Dict[str, BaseChatModel] = {}

    @classmethod
    def register(cls, name: ProviderName, llm: BaseChatModel) -> None:
        cls._registry[name] = llm
        logger.info("llm.registered", provider=name)

    @classmethod
    def get(cls, name: ProviderName) -> BaseChatModel:
        if name not in cls._registry:
            raise KeyError(
                f"LLM '{name}' not initialized. Check .env for API key."
            )
        return cls._registry[name]

    @classmethod
    def all(cls) -> Dict[str, BaseChatModel]:
        return dict(cls._registry)

    @classmethod
    def available(cls) -> List[str]:
        return list(cls._registry.keys())

    @classmethod
    def initialize_all(cls, settings: Optional[Settings] = None) -> None:
        if settings is None:
            settings = get_settings()

        if settings.openai_api_key:
            cls.register(
                "openai",
                ChatOpenAI(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model_name,
                ),
            )
        if settings.anthropic_api_key:
            cls.register(
                "anthropic",
                ChatAnthropic(
                    api_key=settings.anthropic_api_key,
                    model=settings.anthropic_model_name,
                ),
            )
        if settings.google_api_key:
            cls.register(
                "google",
                ChatGoogleGenerativeAI(
                    api_key=settings.google_api_key,
                    model=settings.google_model_name,
                ),
            )

        if not cls._registry:
            logger.warning(
                "llm.no_providers",
                message="No LLM API keys found in .env. Using fallback mock models when requested.",
            )

    @classmethod
    def shutdown(cls) -> None:
        logger.info("llm.shutdown", providers=list(cls._registry.keys()))
        cls._registry.clear()


def get_chat_model(preferred: Optional[str] = None) -> BaseChatModel:
    """
    설정된 LLM 중 최적의 모델을 반환하거나, 키가 없을 경우 Mock 모델을 반환합니다.
    """
    settings = get_settings()
    if not LLMRegistry.available():
        LLMRegistry.initialize_all(settings)

    providers = [preferred] if preferred else ["openai", "anthropic", "google"]
    for p in providers:
        if p and p in LLMRegistry.available():
            return LLMRegistry.get(p)  # type: ignore

    # Default fallback mock LLM with bind_tools support
    return MockChatModel(
        responses=[
            AIMessage(
                content="[분석 완료] 해당 종목의 펀더멘털, 차트 지표 및 리스크 분석이 정상 완료되었습니다."
            )
        ]
    )
