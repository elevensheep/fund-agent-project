from functools import lru_cache
from typing import Dict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 전역 설정 관리자"""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # LLM Model Names
    openai_model_name: str = "gpt-4o"
    anthropic_model_name: str = "claude-3-5-sonnet-20241022"
    google_model_name: str = "gemini-3.6-flash"
    default_llm_provider: str = ""

    # App Metadata
    app_name: str = "A2A Client Server"
    debug: bool = False
    log_level: str = "INFO"

    # Remote A2A Sub-Agents Map (e.g. '{"echo": "http://localhost:28001"}')
    a2a_agents: Dict[str, str] = {}
    
    # MCP Server
    mcp_server_url: str = "http://agent_mcp_server:28002"



@lru_cache
def get_settings() -> Settings:
    return Settings()
