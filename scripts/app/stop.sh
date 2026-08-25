#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🛑 Stopping API Services..."
docker compose -f "$ROOT_DIR/app/docker-compose.yml" down

echo "✅ API services stopped."
