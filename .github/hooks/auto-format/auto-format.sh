#!/usr/bin/env bash
set -euo pipefail

# auto-format — PostToolUse hook
# Best-effort formatting after file writes. Never blocks (always exits 0).

FILE="${TOOL_ARG_FILE_PATH:-${1:-}}"

if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  exit 0
fi

EXT="${FILE##*.}"

# Python files — black + isort
if [[ "$EXT" == "py" ]]; then
  if command -v black &>/dev/null; then
    black --quiet "$FILE" 2>/dev/null || true
  fi
  if command -v isort &>/dev/null; then
    isort --quiet "$FILE" 2>/dev/null || true
  fi
  exit 0
fi

# Protocol Buffer files — buf
if [[ "$EXT" == "proto" ]]; then
  if command -v buf &>/dev/null; then
    buf format -w "$FILE" 2>/dev/null || true
  fi
  exit 0
fi

# GraphQL files — prettier
if [[ "$EXT" == "graphql" ]]; then
  if command -v prettier &>/dev/null; then
    prettier --write "$FILE" 2>/dev/null || true
  fi
  exit 0
fi

exit 0
