#!/bin/bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "🛑 Stopping Full Agent Ecosystem..."
echo "=================================================="

# 의존성 역순으로 종료
echo ""
bash "$ROOT_DIR/scripts/frontend/stop.sh"

echo ""
bash "$ROOT_DIR/scripts/app/stop.sh"

echo ""
bash "$ROOT_DIR/scripts/agent_server/stop.sh"

echo ""
bash "$ROOT_DIR/scripts/mcp_server/stop.sh"

echo ""
bash "$ROOT_DIR/scripts/monitoring/stop.sh"

echo ""
echo "=================================================="
echo "✅ All services stopped."
echo "💡 Note: Data volumes are preserved."
echo "=================================================="
