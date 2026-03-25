#!/usr/bin/env bash
# Rebuild and restart the backend (e.g. after code changes).
# Usage: ./scripts/rebuild.sh
set -euo pipefail

cd "$(dirname "$0")/.."
# shellcheck source=scripts/_load_env.sh
source scripts/_load_env.sh

PROVIDER="${LLM_PROVIDER:-gemini}"
if [[ "$PROVIDER" == "gemini" && -z "${GEMINI_API_KEY:-}" ]]; then
  echo "ERROR: GEMINI_API_KEY is not set." >&2
  exit 1
elif [[ "$PROVIDER" == "anthropic" && -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "ERROR: ANTHROPIC_API_KEY is not set." >&2
  exit 1
fi

docker compose up -d --build

echo ""
echo "  Backend API  : http://localhost:8000"
echo "  API docs     : http://localhost:8000/docs"
echo ""
echo "  Frontend (Flutter):"
echo "    iOS / macOS   cd frontend && flutter run"
echo "    Android       cd frontend && flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000"
echo ""
