#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🎨 Starting Frontend Dashboard..."
docker compose -f "$ROOT_DIR/frontend/docker-compose.yml" up -d --build

echo ""
echo "✅ Frontend Dashboard started!"
echo "  - Web Client (Next.js) : http://localhost:3000"
docker compose -f "$ROOT_DIR/frontend/docker-compose.yml" ps
