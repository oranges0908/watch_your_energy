#!/usr/bin/env bash
# Copy the SQLite database out of the Docker volume to a local backup file.
# Usage: ./scripts/backup_db.sh [output_path]
#   output_path  defaults to ./backups/watch_your_energy_<timestamp>.db
set -euo pipefail

cd "$(dirname "$0")/.."

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT="${1:-backups/watch_your_energy_${TIMESTAMP}.db}"

mkdir -p "$(dirname "$OUTPUT")"

# Run a temporary container that mounts the same volume and copies the file out
docker run --rm \
  -v watchyourenergy_db_data:/data \
  -v "$(pwd)/$(dirname "$OUTPUT"):/backup" \
  python:3.11-slim \
  cp /data/watch_your_energy.db "/backup/$(basename "$OUTPUT")"

echo "Backup saved to: $OUTPUT"
