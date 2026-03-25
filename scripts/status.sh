#!/usr/bin/env bash
# Show container status and do a quick health check against /docs.
# Usage: ./scripts/status.sh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Container status ==="
docker compose ps

echo ""
echo "=== Health check ==="
if curl -sf http://localhost:8000/docs > /dev/null 2>&1; then
  echo "OK — http://localhost:8000/docs is reachable"
else
  echo "UNREACHABLE — backend may still be starting, or not running"
fi
