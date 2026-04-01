---
name: debug
description: >-
  Diagnose failing Uptempo runs, broken schema generation flows, protocol routing
  mistakes, validation failures, or runtime/tooling mismatches before making a fix.
---

# debug

Use this skill when the current issue is primarily about understanding a failure
before changing code.

## Procedure

1. Reproduce the failure with the smallest useful command or workflow.
2. Capture the concrete signal: stack trace, failing validation, malformed schema,
   wrong protocol choice, or broken runtime behavior.
3. Narrow the fault to one layer at a time:
   - WORKFLOW/config parsing
   - tracker/Linear integration
   - workspace lifecycle and hooks
   - Codex app-server / agent runner
   - schema generators and validators
   - PR / handoff automation
4. Prefer direct evidence over guesses.
5. Record the reproduction signal and likely root cause in the workpad before fixing.
6. After the fix, rerun the failing proof and the relevant regression tests.

## Guardrails

- Do not "fix" an issue you have not reproduced unless reproduction is impossible.
- Do not leave temporary debug edits in the final commit.
- If the failure is caused by missing auth, permissions, or third-party outage, document it precisely and stop at the blocker boundary.
