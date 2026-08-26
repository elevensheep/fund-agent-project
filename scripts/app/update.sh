#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔄 Updating API Services..."
echo "🔨 Rebuilding images..."
docker compose -f "$ROOT_DIR/app/docker-compose.yml" build

echo "🚀 Restarting containers..."
docker compose -f "$ROOT_DIR/app/docker-compose.yml" up -d --remove-orphans

echo "✅ API services updated!"
docker compose -f "$ROOT_DIR/app/docker-compose.yml" ps
