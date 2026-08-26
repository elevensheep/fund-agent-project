#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔄 Updating MCP Server..."
docker compose -f "$ROOT_DIR/mcp_server/docker-compose.yml" build
docker compose -f "$ROOT_DIR/mcp_server/docker-compose.yml" up -d --remove-orphans

echo "✅ MCP server updated!"
docker compose -f "$ROOT_DIR/mcp_server/docker-compose.yml" ps
