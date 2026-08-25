#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🛑 Stopping Monitoring Stack..."
docker compose -f "$ROOT_DIR/monitoring/docker-compose.yml" down

echo "✅ Monitoring stack stopped."
