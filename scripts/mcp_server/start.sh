#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔌 Starting MCP Server..."
docker compose -f "$ROOT_DIR/mcp_server/docker-compose.yml" up -d --build

echo ""
echo "✅ MCP server started!"
echo "  - MCP Server (SSE) : http://localhost:28002"
docker compose -f "$ROOT_DIR/mcp_server/docker-compose.yml" ps
