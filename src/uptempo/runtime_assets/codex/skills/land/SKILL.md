---
name: land
description: >-
  Complete the merge path for Uptempo work when a ticket reaches `Merging`.
  Use for final checks, GitHub merge, and post-merge cleanup.
---

# land

Use this skill only when the issue is in `Merging` or a human explicitly requests landing.

## Procedure

1. Reconfirm the PR is the correct one for the issue.
2. Verify approvals and required checks are still green.
3. Sync the branch with the latest `origin/main` if needed and rerun required validation.
4. Merge using `gh pr merge` with the repo-preferred strategy.
5. Confirm the default branch contains the merged commit.
6. Update the issue to `Done` and record merge evidence.
7. Clean up the merged worktree/branch if safe.

## Guardrails

- Do not merge while checks are failing.
- Do not land the wrong PR just because branch names look similar.
- If merge is blocked by policy, record the blocker precisely and stop.
