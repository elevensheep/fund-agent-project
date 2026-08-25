from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """A2A Agent Server 전역 설정"""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # LLM Model Names
    openai_model_name: str = "gpt-4o"
    anthropic_model_name: str = "claude-3-5-sonnet-20241022"
    google_model_name: str = "gemini-3.6-flash"

    # App Metadata
    app_name: str = "A2A Agent Server"
    debug: bool = False
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
