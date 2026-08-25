from typing import Dict, Any
from mcp import ClientSession
from mcp.client.sse import sse_client
from shared_core.logger import logger
import json

async def discover_agents_via_mcp(mcp_server_url: str) -> tuple[Dict[str, str], Dict[str, Any]]:
    """
    MCP Server에 접속하여 list_agent_cards를 호출하고,
    탐색된 에이전트들의 주소(URL) 및 Agent-Card 정보를 동적으로 읽어옵니다.
    반환값: (remote_agents, agent_cards)
    """
    remote_agents: Dict[str, str] = {}
    agent_cards: Dict[str, Any] = {}
    
    if not mcp_server_url:
        return remote_agents, agent_cards

    try:
        url = f"{mcp_server_url.rstrip('/')}/sse"
        async with sse_client(url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                result = await session.call_tool("list_agent_cards", arguments={})
                card_list = []
                
                struct = getattr(result, "structured_content", None)
                if isinstance(struct, dict) and "result" in struct and isinstance(struct["result"], list):
                    card_list = struct["result"]
                elif isinstance(struct, list):
                    card_list = struct

                if not card_list and hasattr(result, "content") and result.content:
                    for item in result.content:
                        text_val = getattr(item, "text", "")
                        if text_val:
                            try:
                                parsed = json.loads(text_val)
                                if isinstance(parsed, list):
                                    card_list.extend(parsed)
                                elif isinstance(parsed, dict):
                                    card_list.append(parsed)
                            except Exception:
                                pass

                for card in card_list:
                    if isinstance(card, dict):
                        name = card.get("name") or card.get("id")
                        interfaces = card.get("supportedInterfaces", [])
                        agent_url = None
                        if interfaces and isinstance(interfaces, list):
                            agent_url = interfaces[0].get("url")
                        
                        if name and agent_url:
                            remote_agents[name] = agent_url
                            short_name = name.replace("_agent", "")
                            remote_agents[short_name] = agent_url
                            card_json = json.dumps(card, ensure_ascii=False)
                            agent_cards[name] = card_json
                            agent_cards[short_name] = card_json
                            logger.info("mcp_client.discovered_agent", agent=name, url=agent_url)
    except Exception as e:
        logger.error("mcp_client.discovery_failed", url=mcp_server_url, error=str(e))
        
    return remote_agents, agent_cards


async def fetch_all_agent_cards(mcp_server_url: str, agents: Dict[str, str]) -> Dict[str, Any]:
    cards = {}
    if not mcp_server_url:
        return cards
        
    discovered_agents, discovered_cards = await discover_agents_via_mcp(mcp_server_url)
    if discovered_cards:
        return discovered_cards

    try:
        url = f"{mcp_server_url.rstrip('/')}/sse"
        async with sse_client(url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                for name, agent_url in agents.items():
                    try:
                        result = await session.call_tool("get_agent_card", arguments={"base_url": agent_url})
                        if hasattr(result, "content") and result.content:
                            text_val = result.content[0].text
                            try:
                                parsed = json.loads(text_val)
                                cards[name] = json.dumps(parsed, ensure_ascii=False)
                            except Exception:
                                cards[name] = text_val
                        else:
                            cards[name] = str(result)
                    except Exception as e:
                        logger.warning("mcp_client.fetch_card_failed", agent=name, error=str(e))
                        cards[name] = None
    except Exception as e:
        logger.error("mcp_client.connection_failed", url=mcp_server_url, error=str(e))
        
    return cards
