import os
from mcp.server.fastmcp import FastMCP
from tools.agent_card import register_tools
from shared_core.logger import logger

port = int(os.environ.get("PORT", 28002))
mcp = FastMCP("A2A Agent MCP Server", host="0.0.0.0", port=port)
register_tools(mcp)

if __name__ == "__main__":
    logger.info("mcp_server.startup", port=port, transport="sse")
    mcp.run(transport="sse")
