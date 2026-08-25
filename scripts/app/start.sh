#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "⚡ Starting Orchestrator App..."
docker compose -f "$ROOT_DIR/app/docker-compose.yml" up -d --build

echo ""
echo "✅ Orchestrator App started!"
echo "  - Orchestrator (app) : http://localhost:28000"
docker compose -f "$ROOT_DIR/app/docker-compose.yml" ps
