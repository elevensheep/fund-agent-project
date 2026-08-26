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
    google_model_name: str = "gemini-2.5-flash"
    default_llm_provider: str = ""

    # App Metadata
    app_name: str = "A2A Agent Server"
    debug: bool = False
    log_level: str = "INFO"

    # PostgreSQL Database Settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "agent_stock_db"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres_secure_pw"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Korea Investment & Securities (KIS) API Settings
    kis_app_key: str = ""
    kis_app_secret: str = ""
    kis_account_no: str = ""
    kis_is_paper_trading: bool = False  # True: 모의투자, False: 실전투자
    kis_ws_url: str = "ws://ops.koreainvestment.com:21000/tryitout/H0STCNT0"
    kis_rest_url: str = "https://openapi.koreainvestment.com:9443"


@lru_cache
def get_settings() -> Settings:
    return Settings()
