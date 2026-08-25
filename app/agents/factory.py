from typing import Dict, Optional
import httpx
from langchain_core.language_models import BaseChatModel

from agents.supervisor import SupervisorAgent
from core.config import Settings, get_settings
from core.llm import LLMRegistry
from shared_core.logger import logger


class AgentFactory:
    """
    A2A Client Agent Factory.
    SupervisorAgent 등 에이전트를 조립 및 반환하는 팩토리 클래스입니다.
    """

    @classmethod
    def create_supervisor(
        cls,
        settings: Optional[Settings] = None,
        llm: Optional[BaseChatModel] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        mcp_server_url: Optional[str] = None,
        remote_agents: Optional[Dict[str, str]] = None,
    ) -> SupervisorAgent:
        """
        SupervisorAgent 구성 및 조립

        Args:
            settings: Settings 애플리케이션 전역 설정 객체
            llm: 사용할 BaseChatModel 객체 (미지정시 LLMRegistry.get_default() 활용)
            http_client: Remote A2A 에이전트 호출용 httpx.AsyncClient
            mcp_server_url: MCP Server SSE endpoint (미지정시 settings.mcp_server_url 사용)
            remote_agents: 수동 지정 원격 에이전트 맵 (미지정시 settings.a2a_agents 사용)

        Returns:
            SupervisorAgent
        """
        if settings is None:
            settings = get_settings()

        if llm is None:
            preferred = getattr(settings, "default_llm_provider", "")
            llm = LLMRegistry.get_default(preferred=preferred)

        target_mcp_url = mcp_server_url or getattr(settings, "mcp_server_url", "http://localhost:28002")
        target_remote_agents = (
            remote_agents
            if remote_agents is not None
            else dict(getattr(settings, "a2a_agents", {}) or {})
        )

        logger.info(
            "agent_factory.supervisor_created",
            initial_agents=list(target_remote_agents.keys()),
            mcp_server_url=target_mcp_url,
            llm_class=llm.__class__.__name__,
        )

        return SupervisorAgent(
            llm=llm,
            remote_agents=target_remote_agents,
            http_client=http_client,
            mcp_server_url=target_mcp_url,
        )

    @classmethod
    def get_supervisor(
        cls,
        registry: Optional[type[LLMRegistry]] = None,
        settings: Optional[Settings] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        mcp_server_url: Optional[str] = None,
    ) -> SupervisorAgent:
        """
        기존 호출 인터페이스 호환용 하위 호환 메서드
        """
        return cls.create_supervisor(
            settings=settings,
            http_client=http_client,
            mcp_server_url=mcp_server_url,
        )
