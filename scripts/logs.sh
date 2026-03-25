#!/usr/bin/env bash
# Tail backend logs.
# Usage: ./scripts/logs.sh [-n <lines>]
#   -n  number of historical lines to show before following (default: 50)
set -euo pipefail

cd "$(dirname "$0")/.."

LINES=50
while getopts "n:" opt; do
  case $opt in
    n) LINES="$OPTARG" ;;
    *) echo "Usage: $0 [-n lines]" >&2; exit 1 ;;
  esac
done

docker compose logs --follow --tail="$LINES" backend
