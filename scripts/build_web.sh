#!/usr/bin/env bash
# Build the Flutter web app and output to frontend/build/web/.
# Run this before `docker compose up` to refresh the frontend.
#
# Usage: ./scripts/build_web.sh [--api-url <url>]
#   --api-url   Backend base URL seen by the browser (default: http://localhost:8000)
set -euo pipefail

cd "$(dirname "$0")/.."
# shellcheck source=scripts/_load_env.sh
source scripts/_load_env.sh

API_URL="http://localhost:8000"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-url) API_URL="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

echo "Building Flutter web (API_BASE_URL=$API_URL) ..."
cd frontend
flutter build web --release \
  --dart-define=API_BASE_URL="$API_URL"

echo ""
echo "Build output: frontend/build/web/"
echo "Start the stack with:  ./scripts/start.sh"
echo "Then open:             http://localhost:3000"
