import json
from typing import AsyncGenerator, Dict, Any

from agents.supervisor import SupervisorAgent
from api.v1.orchestrator.schema import InvokeRequest, InvokeResponse
from shared_core.logger import logger


class OrchestratorService:
    @staticmethod
    async def invoke(body: InvokeRequest, supervisor: SupervisorAgent) -> InvokeResponse:
        logger.info("api.v1.orchestrator.invoke", message=body.message, thread_id=body.thread_id)
        result = await supervisor.ainvoke(body.model_dump())
        return InvokeResponse(
            output=result.get("output", ""),
            used_agents=result.get("used_agents", []),
            remote_response=result.get("remote_response"),
        )

    @staticmethod
    async def stream(body: InvokeRequest, supervisor: SupervisorAgent) -> AsyncGenerator[str, None]:
        logger.info("api.v1.orchestrator.stream", message=body.message, thread_id=body.thread_id)
        async for chunk in supervisor.astream(body.model_dump()):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    @staticmethod
    async def get_info(supervisor: SupervisorAgent) -> Dict[str, Any]:
        await supervisor._ensure_agent_cards()
        return {
            "name": supervisor.name,
            "llm_provider": supervisor.llm.__class__.__name__,
            "remote_agents": supervisor.remote_agents,
            "agent_cards": supervisor.agent_cards,
        }
