---
name: push
description: >-
  Publish the active Uptempo branch after validation passes and keep the remote
  PR branch current.
---

# push

Use this skill after the relevant tests are green and commits are ready.

## Procedure

1. Confirm validation for the current scope is passing.
2. Push the current branch to `origin`.
3. Create or update the PR as needed.
4. Link the PR back to the Linear issue.
5. Keep the workpad aligned with the pushed commit SHA and validation evidence.

## Guardrails

- Never push red builds on purpose.
- Do not push unrelated local experiments.
- If push fails for auth or remote state reasons, document the failure and retry with the safest fix.
