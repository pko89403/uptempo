---
name: linear
description: >-
  Interact with Linear for Uptempo orchestration. Use for fetching issue state,
  maintaining the single Codex workpad comment, transitioning workflow states,
  linking PRs, and creating follow-up issues when scope expands.
---

# linear

Use this skill whenever a task requires reading from or writing to Linear.

## Core rules

- Treat a single `## Codex Workpad` comment as the running source of truth.
- Move states deliberately: `Todo` -> `In Progress` -> `Human Review` -> `Merging` -> `Done`.
- If meaningful out-of-scope work appears, create a separate follow-up issue instead of expanding the current one.
- Keep updates concise and reviewer-oriented.

## Uptempo notes

- The project tracks work through Linear GraphQL at `https://api.linear.app/graphql`.
- Personal API keys use `Authorization: <API_KEY>`.
- Record protocol discovery, rejected alternatives, evidence, and validation in the workpad.
- Attach PR URLs to the issue when possible instead of posting separate summary comments.

## Minimum workflow

1. Read the current issue state and description.
2. Find or create the `## Codex Workpad` comment.
3. Mirror acceptance criteria and validation items into the workpad.
4. Keep the workpad current as implementation changes.
5. Update issue state only when the quality bar for the next state is met.
