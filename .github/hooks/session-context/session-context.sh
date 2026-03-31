#!/usr/bin/env bash
set -euo pipefail

# session-context — sessionStart hook
# Prints project orientation at session start.

echo "╔══════════════════════════════════════════╗"
echo "║        uptempo — session context         ║"
echo "╚══════════════════════════════════════════╝"

# Git worktree & branch
WORKTREE_NAME="$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")"
BRANCH="$(git branch --show-current 2>/dev/null || echo "detached")"
echo ""
echo "  Worktree : $WORKTREE_NAME"
echo "  Branch   : $BRANCH"

# Protocol schema coverage
PROTOCOLS=("rest" "sse" "websocket" "grpc" "graphql" "kafka" "webhook" "mqtt" "trpc")
SCHEMA_DIRS=("src/uptempo/schema" "schemas")

echo ""
echo "  ┌────────────┬───────┬───────┐"
echo "  │ Protocol   │ Files │ State │"
echo "  ├────────────┼───────┼───────┤"

for proto in "${PROTOCOLS[@]}"; do
  COUNT=0
  for dir in "${SCHEMA_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
      FOUND=$(find "$dir" -iname "*${proto}*" -type f 2>/dev/null | wc -l | tr -d ' ')
      COUNT=$((COUNT + FOUND))
    fi
  done
  if [[ "$COUNT" -gt 0 ]]; then
    STATE="  ✅  "
  else
    STATE="  —   "
  fi
  printf "  │ %-10s │ %5s │%s│\n" "$proto" "$COUNT" "$STATE"
done

echo "  └────────────┴───────┴───────┘"

# Reminder
echo ""
echo "  📋 Review .github/copilot-instructions.md for project conventions."
echo ""

exit 0
