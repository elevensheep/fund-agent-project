from typing import Dict, Optional
import httpx
from langchain_core.language_models import BaseChatModel

from agents.dispatcher import ParallelDispatcher
from agents.planner import PlannerAgent
from agents.supervisor import SupervisorAgent
from agents.synthesizer import SynthesizerAgent
from core.config import Settings, get_settings
from core.llm import LLMRegistry
from shared_core.logger import logger


class AgentFactory:
    """
    A2A Orchestrator Agent Factory.
    SupervisorAgent, Planner, Dispatcher, Synthesizer 등 핵심 에이전트를 조립 및 반환하는 팩토리.
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
        if settings is None:
            settings = get_settings()

        if llm is None:
            preferred = getattr(settings, "default_llm_provider", "")
            llm = LLMRegistry.get_default(preferred=preferred)

        target_mcp_url = mcp_server_url or getattr(settings, "mcp_server_url", "http://agent_mcp_server:28002")
        target_remote_agents = (
            remote_agents
            if remote_agents is not None
            else dict(getattr(settings, "a2a_agents", {}) or {})
        )

        planner = PlannerAgent(llm=llm)
        dispatcher = ParallelDispatcher(
            agent_endpoints=target_remote_agents,
            http_client=http_client,
        )
        synthesizer = SynthesizerAgent(llm=llm)

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
            planner=planner,
            dispatcher=dispatcher,
            synthesizer=synthesizer,
        )

    @classmethod
    def get_supervisor(
        cls,
        registry: Optional[type[LLMRegistry]] = None,
        settings: Optional[Settings] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        mcp_server_url: Optional[str] = None,
    ) -> SupervisorAgent:
        return cls.create_supervisor(
            settings=settings,
            http_client=http_client,
            mcp_server_url=mcp_server_url,
        )
