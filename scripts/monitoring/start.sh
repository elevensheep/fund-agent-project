#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "📊 Starting Monitoring Stack (Loki + Promtail + Grafana)..."
docker compose -f "$ROOT_DIR/monitoring/docker-compose.yml" up -d

echo ""
echo "✅ Monitoring stack started!"
echo "  - Grafana : http://localhost:23000 (admin / admin)"
echo "  - Loki    : http://localhost:23100"
docker compose -f "$ROOT_DIR/monitoring/docker-compose.yml" ps
