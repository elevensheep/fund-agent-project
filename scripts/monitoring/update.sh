#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔄 Updating Monitoring Stack..."
docker compose -f "$ROOT_DIR/monitoring/docker-compose.yml" up -d --remove-orphans

echo "✅ Monitoring stack updated!"
docker compose -f "$ROOT_DIR/monitoring/docker-compose.yml" ps
