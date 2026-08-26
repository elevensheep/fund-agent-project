#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🛑 Stopping MCP Server..."
docker compose -f "$ROOT_DIR/mcp_server/docker-compose.yml" down

echo "✅ MCP server stopped."
