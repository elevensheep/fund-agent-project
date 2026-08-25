from typing import Dict, List, Literal
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
