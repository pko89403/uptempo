---
name: session-context
description: Displays project context and protocol schema coverage at the start of every Copilot session
tags: [context, session, sessionStart]
---

# session-context

A **sessionStart** hook that prints project orientation when a new Copilot session begins.

## What it shows

- Current git worktree name and branch
- Protocol schema coverage table (REST, SSE, WebSocket, gRPC, GraphQL, Kafka, Webhook, MQTT, tRPC)
- Reminder to review `.github/copilot-instructions.md`

## Behavior

- Runs once when a Copilot session starts.
- **Always exits 0** — informational only, never blocks.

## Usage

Registered automatically via the root `.github/hooks/hooks.json`.
