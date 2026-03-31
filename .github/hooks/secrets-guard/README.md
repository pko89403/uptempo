---
name: secrets-guard
description: Blocks file writes and commands that contain secrets, API keys, or private key material
tags: [security, secrets, PreToolUse]
---

# secrets-guard

A **PreToolUse** hook that scans content *before* it is written or executed, blocking actions that contain sensitive material.

## Detected patterns

| Category | Examples |
|----------|----------|
| API keys | `sk-*`, `xoxb-*`, `ghp_*`, `AKIA*` |
| Private keys | `BEGIN RSA PRIVATE KEY`, `BEGIN EC PRIVATE KEY`, `BEGIN OPENSSH PRIVATE KEY` |
| Passwords | `password = "..."`, `passwd=...`, hardcoded credentials |
| .env contents | `DATABASE_URL=`, `SECRET_KEY=`, `API_KEY=` with inline values |

## Behavior

- Runs **before** Copilot writes a file or executes a shell command.
- Exits **0** if content is clean.
- Exits **2** to **block** the action (PreToolUse convention).
- Prints a warning identifying the matched pattern.

## Usage

Registered automatically via the root `.github/hooks/hooks.json`.
