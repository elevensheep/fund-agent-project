#!/bin/bash
set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "🚀 Starting Full Agent Ecosystem..."
echo "=================================================="

# 공유 네트워크 생성 (이미 있으면 무시)
echo "🌐 Creating shared network..."
docker network create agent_shared_net 2>/dev/null || echo "   Network already exists, skipping."

echo ""
bash "$ROOT_DIR/scripts/monitoring/start.sh"

echo ""
bash "$ROOT_DIR/scripts/mcp_server/start.sh"

echo ""
bash "$ROOT_DIR/scripts/agent_server/start.sh"

echo ""
bash "$ROOT_DIR/scripts/app/start.sh"

echo ""
echo "=================================================="
echo "✅ All services are up!"
echo "--------------------------------------------------"
echo "🔌 Endpoints:"
echo "  - Orchestrator (app)        : http://localhost:28000"
echo "  - Echo Agent Server (A2A)   : http://localhost:28001"
echo "  - MCP Server (SSE)          : http://localhost:28002"
echo "  - LangChain Agent Server    : http://localhost:28003"
echo "  - Grafana (Logs GUI)        : http://localhost:23000  (admin / admin)"
echo "=================================================="
