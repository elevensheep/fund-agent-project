#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🛑 Stopping Remote A2A Agent Servers..."
docker compose -f "$ROOT_DIR/agent_server/docker-compose.yml" down

echo "✅ Agent servers stopped."
