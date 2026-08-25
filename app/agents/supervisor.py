import json
import uuid
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool

from shared_core.logger import logger
from shared_core.prompt import load_prompt
from core.mcp_client import fetch_all_agent_cards, discover_agents_via_mcp
from .base import BaseAgent


class SupervisorAgent(BaseAgent):
    """
    A2A Client Supervisor Agent.
    Client 서버의 단일 Supervisor로서 사용자 요청을 받아,
    필요시 등록된 Remote A2A Agent에 작업을 위임하고 결과를 종합하여 응답합니다.
    """


    def __init__(
        self,
        llm: BaseChatModel,
        remote_agents: Optional[Dict[str, str]] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        mcp_server_url: str = "http://localhost:28002",
    ) -> None:
        super().__init__()
        self.llm = llm
        self.remote_agents = remote_agents or {}  # name -> url
        self.http_client = http_client or httpx.AsyncClient(timeout=30.0)
        self.mcp_server_url = mcp_server_url
        self.agent_cards = {}
        self._cards_fetched = False

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
        if agent_name not in self.remote_agents:
            return f"Error: Remote agent '{agent_name}' is not registered."

        url = self.remote_agents[agent_name]
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        logger.info("task.supervisor.call_remote_agent", target_agent=agent_name, url=url, message=message, msg_id=msg_id)

        # 1. A2A JSON-RPC 2.0 규격 호출 (SendMessage, a2a-version: 1.0)
        jsonrpc_payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "SendMessage",
            "params": {
                "message": {
                    "message_id": msg_id,
                    "role": "ROLE_USER",
                    "parts": [{"text": message}],
                }
            },
        }

        try:
            resp = await self.http_client.post(
                url,
                json=jsonrpc_payload,
                headers={
                    "Content-Type": "application/json",
                    "a2a-version": "1.0",
                },
                timeout=30.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                if "result" in data:
                    res_val = data["result"]
                    if isinstance(res_val, dict):
                        task = res_val.get("task", {}) if isinstance(res_val, dict) else {}
                        status_msg = (
                            task.get("status", {}).get("message", {})
                            if isinstance(task.get("status"), dict)
                            else {}
                        )
                        history = task.get("history", []) if isinstance(task, dict) else []
                        last_history_msg = (
                            history[-1] if history and isinstance(history[-1], dict) else {}
                        )

                        msg = status_msg or last_history_msg or (
                            res_val.get("message", {}) if isinstance(res_val, dict) else {}
                        )
                        parts = msg.get("parts", []) if isinstance(msg, dict) else []
                        texts = [p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p]
                        if texts:
                            return "".join(texts)
                        return json.dumps(res_val, ensure_ascii=False)
                    return str(res_val)
                elif "error" in data:
                    logger.warning("supervisor.jsonrpc_error", agent=agent_name, error=data["error"])
        except Exception as e:
            logger.warning("supervisor.jsonrpc_call_failed", agent=agent_name, error=str(e))

        # 2. REST Direct Fallback
        endpoints_to_try = [
            f"{url.rstrip('/')}/v1/message",
            f"{url.rstrip('/')}/invoke",
        ]

        for endpoint in endpoints_to_try:
            try:
                payloads = [
                    {"message": message},
                    {"text": message},
                ]
                for payload in payloads:
                    resp = await self.http_client.post(
                        endpoint,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=30.0,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, dict) and "jsonrpc" not in data:
                            res_str = (
                                data.get("output")
                                or data.get("content")
                                or data.get("text")
                                or data.get("result")
                            )
                            if res_str:
                                return str(res_str)
                            return json.dumps(data, ensure_ascii=False)
                        elif isinstance(data, str):
                            return data
            except Exception:
                continue

        return f"Failed to communicate with remote agent '{agent_name}' at {url}"

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
        if not self._cards_fetched:
            discovered_agents, discovered_cards = await discover_agents_via_mcp(self.mcp_server_url)
            if discovered_agents:
                self.remote_agents.update(discovered_agents)
                self.agent_cards = discovered_cards
            else:
                self.agent_cards = await fetch_all_agent_cards(self.mcp_server_url, self.remote_agents)
            self._cards_fetched = True
            logger.info("artifact.supervisor.agent_cards_loaded", cards=self.agent_cards, remote_agents=self.remote_agents)

    async def ainvoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Supervisor 비동기 실행.
        inputs: {"message": str, ...}
        """
        await self._ensure_agent_cards()
        
        user_message = inputs.get("message", "")
        logger.info("task.supervisor.start", message=user_message)

        tools = self._build_tools()
        if tools and hasattr(self.llm, "bind_tools"):
            try:
                llm_with_tools = self.llm.bind_tools(tools)
            except NotImplementedError:
                llm_with_tools = self.llm
        else:
            llm_with_tools = self.llm

        messages: List[BaseMessage] = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=user_message),
        ]

        response = await llm_with_tools.ainvoke(messages)

        used_agents = []
        remote_responses = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            messages.append(response)
            for tool_call in response.tool_calls:
                fn_name = tool_call.get("name", "")
                args = tool_call.get("args", {})
                msg_to_send = args.get("msg") or args.get("message") or user_message

                target_agent = fn_name.replace("delegate_to_", "")
                logger.info("task.supervisor.execute_remote_tool", tool=fn_name, target_agent=target_agent, message=msg_to_send)
                if target_agent in self.remote_agents:
                    used_agents.append(target_agent)
                    agent_res = await self.call_remote_agent(target_agent, msg_to_send)
                    remote_responses.append(agent_res)
                    messages.append(
                        HumanMessage(
                            content=f"Remote agent '{target_agent}' returned: {agent_res}."
                        )
                    )

            if used_agents:
                messages.append(
                    HumanMessage(
                        content="Synthesize all remote agent responses and provide a helpful final response to the user."
                    )
                )
                final_response = await self.llm.ainvoke(messages)
                formatted_output = self._format_content(final_response.content)
                logger.info("task.supervisor.completed", output=formatted_output, used_agents=used_agents)
                logger.info("artifact.supervisor.output_created", output=formatted_output, used_agents=used_agents)
                return {
                    "output": formatted_output,
                    "used_agents": used_agents,
                    "remote_response": "\n".join(remote_responses),
                }

        formatted_output = self._format_content(response.content)
        logger.info("task.supervisor.completed", output=formatted_output, used_agents=used_agents)
        logger.info("artifact.supervisor.output_created", output=formatted_output, used_agents=used_agents)
        return {
            "output": formatted_output,
            "used_agents": used_agents,
        }

    async def astream(self, inputs: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """Supervisor 토큰 비동기 스트리밍 (Remote Agent Tool Call 연동)"""
        await self._ensure_agent_cards()
        
        user_message = inputs.get("message", "")
        logger.info("supervisor.astream.start", message=user_message)

        tools = self._build_tools()
        if tools and hasattr(self.llm, "bind_tools"):
            try:
                llm_with_tools = self.llm.bind_tools(tools)
            except NotImplementedError:
                llm_with_tools = self.llm
        else:
            llm_with_tools = self.llm

        messages: List[BaseMessage] = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=user_message),
        ]

        response = await llm_with_tools.ainvoke(messages)
        if hasattr(response, "tool_calls") and response.tool_calls:
            messages.append(response)
            for tool_call in response.tool_calls:
                fn_name = tool_call.get("name", "")
                args = tool_call.get("args", {})
                msg_to_send = args.get("msg") or args.get("message") or user_message
                target_agent = fn_name.replace("delegate_to_", "")
                
                logger.info("supervisor.execute_remote_tool", tool=fn_name, target_agent=target_agent, args=args)
                
                if target_agent in self.remote_agents:
                    agent_res = await self.call_remote_agent(target_agent, msg_to_send)
                    messages.append(
                        HumanMessage(
                            content=f"Remote agent '{target_agent}' returned: {agent_res}."
                        )
                    )
            messages.append(
                HumanMessage(
                    content="Synthesize all remote agent responses and provide a helpful final response to the user."
                )
            )
            async for chunk in self.llm.astream(messages):
                yield {"token": self._format_content(chunk.content)}
        else:
            yield {"token": self._format_content(response.content)}
