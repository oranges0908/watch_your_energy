#!/usr/bin/env bash
# Sourced by other scripts — do not execute directly.
# Loads .env from the repo root if present, without overriding existing shell vars.

_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$_REPO_ROOT/.env" ]]; then
  # Export only lines that are KEY=VALUE (skip comments and blanks),
  # and only when the variable is not already set in the environment.
  while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    key="${line%%=*}"
    if [[ -z "${!key:-}" ]]; then
      export "$line"
    fi
  done < "$_REPO_ROOT/.env"
fi
