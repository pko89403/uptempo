#!/usr/bin/env bash
set -euo pipefail

# secrets-guard — PreToolUse hook
# Scans content for secrets before file writes or command execution.
# Exit 2 = BLOCK the action (PreToolUse convention).

CONTENT="${TOOL_ARG_CONTENT:-${TOOL_ARG_COMMAND:-${1:-}}}"

if [[ -z "$CONTENT" ]]; then
  exit 0
fi

# Patterns to detect — each entry is "label|regex"
PATTERNS=(
  "OpenAI/Stripe API key|sk-[A-Za-z0-9]{20,}"
  "Slack token|xoxb-[A-Za-z0-9-]+"
  "GitHub PAT|ghp_[A-Za-z0-9]{36}"
  "AWS Access Key|AKIA[0-9A-Z]{16}"
  "RSA private key|BEGIN RSA PRIVATE KEY"
  "EC private key|BEGIN EC PRIVATE KEY"
  "OpenSSH private key|BEGIN OPENSSH PRIVATE KEY"
  "Hardcoded password|password\s*=\s*[\"'][^\"']+[\"']"
  "Hardcoded passwd|passwd\s*=\s*[\"'][^\"']+[\"']"
  "DATABASE_URL with value|DATABASE_URL=[\"']?[a-zA-Z]+://"
  "SECRET_KEY with value|SECRET_KEY=[\"']?[A-Za-z0-9]"
  "Inline API_KEY value|API_KEY=[\"']?[A-Za-z0-9]"
)

for entry in "${PATTERNS[@]}"; do
  LABEL="${entry%%|*}"
  REGEX="${entry#*|}"
  if echo "$CONTENT" | grep -qEi "$REGEX"; then
    echo "🚫 secrets-guard: Blocked — detected $LABEL"
    echo "   Remove the secret before proceeding."
    exit 2
  fi
done

exit 0
