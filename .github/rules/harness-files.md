---
description: "Enforce frontmatter format, naming conventions, and progressive disclosure for agents and skills"
paths:
  - ".github/agents/**/*.md"
  - ".github/skills/**/*.md"
  - ".github/hooks/**/*"
  - ".github/workflows/**/*.md"
  - ".github/rules/**/*.md"
priority: 15
---

# Harness File Rules

## Agents

- Include YAML frontmatter with `name`, `description`, `model`, and `tools` fields.
- Use lowercase-hyphenated names (e.g., `api-architect`, `grpc-engineer`).
- Leave `model` empty unless a specific model is required.
- Keep agent files under 300 lines.

## Skills

- Name the file `SKILL.md` inside a folder named after the skill.
- Include `name` and `description` in the frontmatter.
- Start the description with a verb describing the trigger condition ("pushy" style), in one sentence.
- Follow Progressive Disclosure: metadata (~100 words) → body (<500 lines) → `references/` (unlimited).
- Keep skill files under 500 lines.

## Hooks

- Start every hook script with `#!/usr/bin/env bash` and `set -euo pipefail`.
- Include a `README.md` with frontmatter containing `name`, `description`, and `tags`.

## Workflows

- Include frontmatter with `name`, `description`, and `on` (trigger definition).

## Rules

- Include frontmatter with `description`, `paths`, and `priority`.

## General

- Write all content in English.
- Never use inline HTML in markdown files.
