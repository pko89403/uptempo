---
name: schema-lint
description: Validates network schema files (proto, OpenAPI, GraphQL, Python) on every write
tags: [lint, schema, validation, PostToolUse]
---

# schema-lint

A **PostToolUse** hook that automatically validates schema files whenever they are written.

## Supported file types

| Extension | Path constraint | Validation |
|-----------|----------------|------------|
| `.py` | `src/uptempo/schema/` | `ruff check --select E,W,F` |
| `.proto` | any | proto3 syntax declaration |
| `.yaml`/`.yml` | `schemas/openapi/` | `openapi:` key present |
| `.graphql` | any | `type Query` or `schema` keyword |

## Behavior

- Runs after Copilot writes a file matching the above patterns.
- Exits **0** on pass, **1** on failure with a descriptive message.
- Only lints files relevant to the uptempo schema system.

## Usage

Registered automatically via the root `.github/hooks/hooks.json`.
