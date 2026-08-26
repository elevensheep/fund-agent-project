#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🤖 Starting Remote A2A Agent Servers (8 Sub-Agents, Postgres, Stream Worker)..."
docker compose -f "$ROOT_DIR/agent_server/docker-compose.yml" up -d --build

echo ""
echo "✅ Agent servers started!"
echo "  - Data Processing Server (A2A)  : http://localhost:28001"
echo "  - Web Search Agent Server       : http://localhost:28003"
echo "  - Fundamental Agent Server      : http://localhost:28004"
echo "  - Technical Agent Server        : http://localhost:28005"
echo "  - DART Disclosure Agent Server  : http://localhost:28006"
echo "  - Macro & Sector Agent Server   : http://localhost:28007"
echo "  - Bull vs Bear Debate Server    : http://localhost:28008"
echo "  - Risk Management Server (Rule) : http://localhost:28009"
echo "  - PostgreSQL Database           : localhost:5432"
docker compose -f "$ROOT_DIR/agent_server/docker-compose.yml" ps
