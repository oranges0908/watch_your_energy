#!/usr/bin/env bash
# Stop the backend containers.
# Usage: ./scripts/stop.sh
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose down
echo "Backend stopped."
