import json
import os
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP

from shared_core.logger import logger

DEFAULT_AGENT_ENDPOINTS: List[str] = [
    url.strip()
    for url in os.environ.get(
        "AGENT_ENDPOINTS",
        "http://agent_data_processing_server:28001,"
        "http://agent_web_search_server:28003,"
        "http://agent_fundamental_server:28004,"
        "http://agent_technical_server:28005,"
        "http://agent_dart_disclosure_server:28006,"
        "http://agent_macro_sector_server:28007,"
        "http://agent_bull_bear_debate_server:28008,"
        "http://agent_risk_management_server:28009",
    ).split(",")
    if url.strip()
]


async def _fetch_single_card(client: httpx.AsyncClient, base_url: str) -> Optional[Dict[str, Any]]:
    """단일 에이전트 서버의 Agent Card를 요청하고 표준 인터페이스 구조를 보장합니다."""
    clean_url = base_url.rstrip("/")
    card_url = f"{clean_url}/.well-known/agent-card.json"
    try:
        resp = await client.get(card_url, timeout=5.0)
        if resp.status_code == 200:
            card_data = resp.json()
            if "supportedInterfaces" not in card_data or not card_data["supportedInterfaces"]:
                card_data["supportedInterfaces"] = [
                    {"url": clean_url, "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}
                ]
            elif isinstance(card_data.get("supportedInterfaces"), list) and card_data["supportedInterfaces"]:
                curr_url = card_data["supportedInterfaces"][0].get("url")
                if curr_url in ["http://localhost:8000", "http://0.0.0.0:8000", "http://127.0.0.1:8000"]:
                    card_data["supportedInterfaces"][0]["url"] = clean_url
            return card_data
    except Exception as e:
        logger.warning("mcp.fetch_card.failed", endpoint=clean_url, error=str(e))
    return None


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_agent_card(base_url: str = "http://agent_data_processing_server:28001") -> dict:
        """
        단일 A2A Agent Server의 Agent Card를 조회합니다.
        """
        logger.info("task.mcp.get_agent_card.started", base_url=base_url)
        async with httpx.AsyncClient() as client:
            card_data = await _fetch_single_card(client, base_url)
            if not card_data:
                card_data = {
                    "name": "unknown",
                    "supportedInterfaces": [
                        {"url": base_url, "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}
                    ],
                }
            logger.info("artifact.mcp.agent_card_retrieved", base_url=base_url, card=card_data)
            return card_data

    @mcp.tool()
    async def list_agent_cards(endpoints: Optional[List[str]] = None) -> str:
        """
        등록된 모든 A2A Agent Server를 탐색하여 Agent Card 목록(JSON 문자열)을 반환합니다.
        각 Card에는 에이전트 이름, 능력, 스킬 및 접속 URL(supportedInterfaces) 정보가 포함됩니다.
        """
        target_endpoints = endpoints or DEFAULT_AGENT_ENDPOINTS
        logger.info("task.mcp.list_agent_cards.started", endpoints=target_endpoints)

        cards: List[Dict[str, Any]] = []
        async with httpx.AsyncClient() as client:
            for url in target_endpoints:
                if not url.strip():
                    continue
                card = await _fetch_single_card(client, url.strip())
                if card:
                    cards.append(card)

        logger.info("artifact.mcp.discovered_agent_cards", count=len(cards), cards=cards)
        return json.dumps(cards, ensure_ascii=False)
