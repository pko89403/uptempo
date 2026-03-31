#!/usr/bin/env bash
set -euo pipefail

# schema-lint — PostToolUse hook
# Validates schema files after they are written.

FILE="${TOOL_ARG_FILE_PATH:-${1:-}}"

if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  exit 0
fi

EXT="${FILE##*.}"

# Python files under src/uptempo/schema/
if [[ "$EXT" == "py" && "$FILE" == *src/uptempo/schema/* ]]; then
  if command -v ruff &>/dev/null; then
    if ! ruff check --select E,W,F --quiet "$FILE"; then
      echo "❌ schema-lint: ruff found issues in $FILE"
      exit 1
    fi
  fi
  exit 0
fi

# Protocol Buffer files
if [[ "$EXT" == "proto" ]]; then
  if ! grep -q 'syntax\s*=\s*"proto3"' "$FILE"; then
    echo "❌ schema-lint: $FILE missing 'syntax = \"proto3\"' declaration"
    exit 1
  fi
  exit 0
fi

# OpenAPI YAML files under schemas/openapi/
if [[ "$EXT" == "yaml" || "$EXT" == "yml" ]] && [[ "$FILE" == *schemas/openapi/* ]]; then
  if ! grep -q '^openapi:' "$FILE"; then
    echo "❌ schema-lint: $FILE missing top-level 'openapi:' key"
    exit 1
  fi
  exit 0
fi

# GraphQL schema files
if [[ "$EXT" == "graphql" ]]; then
  if ! grep -qE '(type\s+Query|^schema\s*\{)' "$FILE"; then
    echo "❌ schema-lint: $FILE missing 'type Query' or 'schema' definition"
    exit 1
  fi
  exit 0
fi

# Not a recognized schema file — pass through
exit 0
