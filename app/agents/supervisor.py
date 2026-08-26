import json
import uuid
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool

from core.mcp_client import discover_agents_via_mcp, fetch_all_agent_cards
from shared_core.logger import logger
from shared_core.prompt import load_prompt
from .base import BaseAgent
from .dispatcher import ParallelDispatcher
from .planner import ExecutionPlan, PlannerAgent
from .synthesizer import SynthesizerAgent


class SupervisorAgent(BaseAgent):
    """
    Plan-and-Execute 아키텍처 기반 중앙 Supervisor 오케스트레이터 에이전트.
    Planner ➡️ Parallel Dispatcher ➡️ Synthesizer 3단계 파이프라인으로
    8대 금융 전문 서브 에이전트를 조율합니다.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        remote_agents: Optional[Dict[str, str]] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        mcp_server_url: str = "http://agent_mcp_server:28002",
        planner: Optional[PlannerAgent] = None,
        dispatcher: Optional[ParallelDispatcher] = None,
        synthesizer: Optional[SynthesizerAgent] = None,
    ) -> None:
        super().__init__()
        self.llm = llm
        self.remote_agents = remote_agents or {}  # name -> url
        self.http_client = http_client or httpx.AsyncClient(timeout=30.0)
        self.mcp_server_url = mcp_server_url
        self.agent_cards = {}
        self._cards_fetched = False

        # Plan-and-Execute 구성요소 초기화
        self.planner = planner or PlannerAgent(llm=self.llm)
        self.dispatcher = dispatcher or ParallelDispatcher(
            agent_endpoints=self.remote_agents,
            http_client=self.http_client,
        )
        self.synthesizer = synthesizer or SynthesizerAgent(llm=self.llm)

    @property
    def name(self) -> str:
        return "supervisor"

    def _get_system_prompt(self) -> str:
        prompt_path = Path(__file__).parent / "prompts" / "supervisor.yml"
        system_prompt = load_prompt(prompt_path, key="system_prompt", default="")

        if not self.remote_agents:
            agent_info = "No remote A2A agents currently registered."
        else:
            info_lines = []
            for name, url in self.remote_agents.items():
                card = self.agent_cards.get(name)
                if card:
                    info_lines.append(f"- Agent '{name}' at {url}\n  Capabilities: {card}")
                else:
                    info_lines.append(f"- Agent '{name}' at {url}")
            agent_info = "\n".join(info_lines)

        return system_prompt.format(agent_info=agent_info)

    def _build_tools(self) -> List[Any]:
        """등록된 Remote Agent를 호출하는 LangChain Tool 리스트 생성"""
        tools = []
        for name, url in self.remote_agents.items():
            agent_name = name
            agent_url = url

            def create_tool(target_name: str, target_url: str):
                async def delegate_task(message: str) -> str:
                    return await self.call_remote_agent(target_name, message)

                delegate_task.__name__ = f"delegate_to_{target_name}"
                delegate_task.__doc__ = (
                    f"Delegate task to remote A2A sub-agent '{target_name}' at {target_url}."
                )
                return tool(delegate_task)

            tools.append(create_tool(agent_name, agent_url))
        return tools

    async def call_remote_agent(self, agent_name: str, message: str) -> str:
        """Remote A2A Agent 호출 (공식 Google ADK A2A JSON-RPC 2.0 Protocol)"""
        from .planner import PlanStep
        step = PlanStep(step_id=1, agent_name=agent_name, task_prompt=message)
        res = await self.dispatcher.call_agent(step)
        return res.get("output", "")

    def _format_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
                else:
                    parts.append(str(item))
            return "".join(parts)
        return str(content)

    async def _ensure_agent_cards(self):
        """MCP 서버를 통해 서브 에이전트 목록 및 Agent Card 동적 탐색"""
        if not self._cards_fetched:
            discovered_agents, discovered_cards = await discover_agents_via_mcp(self.mcp_server_url)
            if discovered_agents:
                self.remote_agents.update(discovered_agents)
                self.agent_cards = discovered_cards
            else:
                self.agent_cards = await fetch_all_agent_cards(self.mcp_server_url, self.remote_agents)
            
            # Dispatcher 엔드포인트 동기화
            self.dispatcher.set_endpoints(self.remote_agents)
            self._cards_fetched = True
            logger.info("artifact.supervisor.agent_cards_loaded", cards=self.agent_cards, remote_agents=self.remote_agents)

    async def ainvoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Supervisor Plan-and-Execute 메인 실행 파이프라인.
        1. Planner: 질의 분석 및 ExecutionPlan 수립
        2. Parallel Dispatcher: 단계별 병렬 A2A 호출
        3. Synthesizer: 종합 리포트 생성
        """
        await self._ensure_agent_cards()

        user_message = inputs.get("message", "")
        logger.info("task.supervisor.plan_and_execute.start", message=user_message)

        # 1. 실행 계획(DAG) 수립
        plan: ExecutionPlan = await self.planner.create_plan(user_message)
        logger.info("task.supervisor.plan_created", ticker=plan.ticker, intent=plan.query_intent, steps=len(plan.steps))

        # 2. 병렬 디스패치 실행
        dispatch_res = await self.dispatcher.execute_plan(plan)
        used_agents = dispatch_res.get("used_agents", [])
        sub_results = dispatch_res.get("sub_agent_results", {})

        # 3. 결과 종합 및 최종 리포트 작성
        final_report = await self.synthesizer.synthesize(
            ticker=plan.ticker,
            intent=plan.query_intent,
            sub_agent_results=sub_results,
            user_query=user_message,
        )

        logger.info("task.supervisor.plan_and_execute.completed", used_agents=used_agents, output_len=len(final_report))
        logger.info("artifact.supervisor.output_created", output=final_report, used_agents=used_agents)

        return {
            "output": final_report,
            "used_agents": used_agents,
            "plan": plan.model_dump(),
            "remote_response": json.dumps(sub_results, ensure_ascii=False),
        }

    async def astream(self, inputs: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """Supervisor 최종 리포트 토큰 비동기 스트리밍"""
        result = await self.ainvoke(inputs)
        output_text = result.get("output", "")
        
        # Word/chunk streaming
        words = output_text.split(" ")
        for i, word in enumerate(words):
            token = word if i == len(words) - 1 else word + " "
            yield {"token": token}
