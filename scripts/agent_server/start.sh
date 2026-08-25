#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🤖 Starting Remote A2A Agent Servers (echo, langchain)..."
docker compose -f "$ROOT_DIR/agent_server/docker-compose.yml" up -d --build

echo ""
echo "✅ Agent servers started!"
echo "  - Echo Agent Server      : http://localhost:28001"
echo "  - LangChain Agent Server : http://localhost:28003"
docker compose -f "$ROOT_DIR/agent_server/docker-compose.yml" ps
