from fastapi import Request, HTTPException
from langchain_core.language_models import BaseChatModel
from core.llm import ProviderName


def get_llm(provider: ProviderName, request: Request) -> BaseChatModel:
    """
    app.state.llm_registry에서 지정된 Provider LLM을 추출하는 FastAPI Dependency Injection 함수.
    """
    try:
        return request.app.state.llm_registry.get(provider)
    except KeyError:
        available = request.app.state.llm_registry.available()
        raise HTTPException(
            status_code=503,
            detail=f"LLM provider '{provider}' not available. Available: {available}",
        )
