#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🛑 Stopping Frontend Dashboard..."
docker compose -f "$ROOT_DIR/frontend/docker-compose.yml" down
echo "✅ Frontend Dashboard stopped."
