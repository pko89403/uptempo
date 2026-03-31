---
description: "Enforce generator patterns and ABC compliance for schema generators"
paths:
  - "src/uptempo/schema/**/*.py"
excludePaths:
  - "src/uptempo/schema/__init__.py"
priority: 10
---

# Schema Generator Rules

- Use `from __future__ import annotations` at the top of every module.
- Inherit all generators from the `SchemaGenerator` base class defined in `base.py`.
- Implement `generate(issue, workspace) -> list[Path]` to produce schema files.
- Implement `validate(files) -> list[str]` to check generated output.
- Return an empty list from `validate` on success; return a list of error strings on failure.
- Use `_header_comment(issue, prefix)` to produce generated-file headers.
- Write generated files to `{workspace}/schemas/{protocol}/`.
- Import `Issue` from `uptempo.tracker.models`.
- Never hardcode file paths — use `pathlib.Path` throughout.
- Keep generators stateless — do not store instance variables beyond config.
- Include type hints on all public methods.
