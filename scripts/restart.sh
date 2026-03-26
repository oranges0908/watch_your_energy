#!/usr/bin/env bash
# Restart containers without rebuilding the image.
# Usage: ./scripts/restart.sh
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose restart
echo "Restarted."
