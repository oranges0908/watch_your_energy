#!/usr/bin/env bash
# !! DESTRUCTIVE !! — wipe the database and start fresh.
# Stops containers, removes the db_data volume, then starts again.
# Usage: ./scripts/reset_db.sh
set -euo pipefail

cd "$(dirname "$0")/.."
# shellcheck source=scripts/_load_env.sh
source scripts/_load_env.sh

echo "WARNING: This will permanently delete all data in the database."
read -r -p "Are you sure? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Aborted."
  exit 0
fi

docker compose down -v
echo "Volume removed."
docker compose up -d
echo "Fresh database started on http://localhost:8000"
