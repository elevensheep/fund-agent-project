#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔄 Updating Remote A2A Agent Servers..."
echo "🔨 Rebuilding images..."
docker compose -f "$ROOT_DIR/agent_server/docker-compose.yml" build

echo "🚀 Restarting containers..."
docker compose -f "$ROOT_DIR/agent_server/docker-compose.yml" up -d --remove-orphans

echo "✅ Agent servers updated!"
docker compose -f "$ROOT_DIR/agent_server/docker-compose.yml" ps
