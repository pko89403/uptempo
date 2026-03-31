---
name: pull
description: >-
  Sync the active worktree with the latest `origin/main` before implementation
  and again before handoff.
---

# pull

Use this skill when starting work, before opening a PR, and before final handoff.

## Procedure

1. Fetch `origin/main`.
2. Rebase or merge onto `origin/main` using the repo-preferred strategy.
3. Resolve conflicts in the current worktree only.
4. Re-run validation if the sync changed executable code.
5. Record sync evidence in the workpad:
   - source branch,
   - clean vs conflict resolution,
   - resulting short SHA.

## Guardrails

- Do not rewrite another agent's worktree.
- If the current branch already has a closed or merged PR, start from a fresh branch instead of reusing it.
