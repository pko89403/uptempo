---
name: commit
description: >-
  Produce clean, logical commits for Uptempo work. Use after validation passes
  and before push or handoff.
---

# commit

Use this skill to package finished work into reviewable commits.

## Commit rules

- Commit coherent units of work; do not mix unrelated edits.
- Run the relevant validation before committing and record the commands/results.
- Keep generated or temporary files out of the commit unless intentionally required.
- Use clear messages that explain the outcome, not the keystrokes.
- Always include the repository trailer:

```text
Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

## Before committing

1. Review `git diff` for accidental files.
2. Revert temporary proof-only edits.
3. Ensure the workpad reflects the completed state.
4. Stage only the intended paths.
