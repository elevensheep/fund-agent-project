from typing import Dict, List, Literal, Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from core.config import Settings
from shared_core.logger import logger

ProviderName = Literal["openai", "anthropic", "google"]


class LLMRegistry:
    """
    Multi-provider LLM Singleton Registry.
    App startup 시 initialize_all()로 초기화되며, app.state.llm_registry로 관리됩니다.
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
    def get_default(cls, preferred: Optional[str] = None) -> BaseChatModel:
        """
        우선순위(preferred) -> openai -> anthropic -> google -> 가용한 첫 번째 LLM 순으로 검색하며,
        등록된 LLM이 없을 경우 Mock LLM을 생성하여 반환합니다.
        """
        if preferred and preferred in cls._registry:
            logger.info("llm.selected_preferred", provider=preferred)
            return cls._registry[preferred]

        for provider in ["openai", "anthropic", "google"]:
            if provider in cls._registry:
                logger.info("llm.selected", provider=provider)
                return cls._registry[provider]

        if cls._registry:
            first = list(cls._registry.keys())[0]
            logger.info("llm.selected_fallback", provider=first)
            return cls._registry[first]

        logger.warning(
            "llm.no_key_found",
            message="No LLM API keys provided. Using mock LLM.",
        )
        from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
        from langchain_core.messages import AIMessage

        return FakeMessagesListChatModel(
            responses=[
                AIMessage(
                    content="[Mock LLM] API Key is not set. Please set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY in .env"
                )
            ]
        )

    @classmethod
    def initialize_all(cls, settings: Settings) -> None:
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
