#!/usr/bin/env bash
# Start the backend in detached mode.
# Usage: ./scripts/start.sh [--build]
set -euo pipefail

cd "$(dirname "$0")/.."
# shellcheck source=scripts/_load_env.sh
source scripts/_load_env.sh

PROVIDER="${LLM_PROVIDER:-gemini}"
if [[ "$PROVIDER" == "gemini" && -z "${GEMINI_API_KEY:-}" ]]; then
  echo "ERROR: GEMINI_API_KEY is not set." >&2
  echo "  Set it in .env or: export GEMINI_API_KEY=<your-key>" >&2
  exit 1
elif [[ "$PROVIDER" == "anthropic" && -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "ERROR: ANTHROPIC_API_KEY is not set." >&2
  echo "  Set it in .env or: export ANTHROPIC_API_KEY=<your-key>" >&2
  exit 1
fi

docker compose up -d ${1:-}

echo ""
echo "  Backend API  : http://localhost:8000"
echo "  API docs     : http://localhost:8000/docs"
echo "  Web frontend : http://localhost:3000"
echo ""
echo "  (Mobile) iOS/macOS : cd frontend && flutter run"
echo "  (Mobile) Android   : cd frontend && flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000"
echo ""
echo "  Run ./scripts/build_web.sh first if the web frontend is not yet built."
echo ""
