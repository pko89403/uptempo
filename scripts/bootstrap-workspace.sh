#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

source_repo="${UPTEMPO_WORKSPACE_SOURCE:-$repo_root}"

if [[ -n "${UPTEMPO_WORKSPACE_SOURCE:-}" && "$source_repo" != /* ]]; then
  candidate="$repo_root/$source_repo"
  if [[ -e "$candidate" ]]; then
    source_repo="$candidate"
  fi
fi

clone_args=(--depth 1)
if [[ -e "$source_repo" ]]; then
  source_repo="$(cd "$source_repo" && pwd)"
  clone_args+=(--no-local)
fi

git clone "${clone_args[@]}" "$source_repo" .
