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
bash "$ROOT_DIR/scripts/frontend/start.sh"

echo ""
echo "=================================================="
echo "✅ All services are up!"
echo "--------------------------------------------------"
echo "🔌 Endpoints:"
echo "  - Frontend Web Dashboard        : http://localhost:3000"
echo "  - Orchestrator (app)            : http://localhost:28000"
echo "  - Data Processing Server (A2A)  : http://localhost:28001"
echo "  - MCP Server (SSE)              : http://localhost:28002"
echo "  - Web Search Agent Server       : http://localhost:28003"
echo "  - Fundamental Agent Server      : http://localhost:28004"
echo "  - Technical Agent Server        : http://localhost:28005"
echo "  - DART Disclosure Agent Server  : http://localhost:28006"
echo "  - Macro & Sector Agent Server   : http://localhost:28007"
echo "  - Bull vs Bear Debate Server    : http://localhost:28008"
echo "  - Risk Management Server (Rule) : http://localhost:28009"
echo "  - PostgreSQL Database           : localhost:5432"
echo "  - Prometheus (Metrics)          : http://localhost:29090"
echo "  - Grafana (Observability GUI)   : http://localhost:23000  (admin / admin)"
echo "=================================================="
