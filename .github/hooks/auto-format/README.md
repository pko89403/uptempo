---
name: auto-format
description: Automatically formats schema and source files after every write using black, isort, buf, prettier
tags: [format, style, PostToolUse]
---

# auto-format

A **PostToolUse** hook that automatically formats files after they are written.

## Supported formatters

| Extension | Formatter | Fallback |
|-----------|-----------|----------|
| `.py` | `black` + `isort` | Skipped if not installed |
| `.proto` | `buf format -w` | Skipped if not installed |
| `.graphql` | `prettier --write` | Skipped if not installed |

## Behavior

- Runs after Copilot writes a file.
- Only invokes formatters that are available (`command -v` check).
- **Always exits 0** — formatting is best-effort and never blocks.

## Usage

Registered automatically via the root `.github/hooks/hooks.json`.
