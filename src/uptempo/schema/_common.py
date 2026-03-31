"""Shared helpers for deterministic schema generation."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uptempo.tracker.models import Issue

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "api",
    "build",
    "create",
    "for",
    "from",
    "generate",
    "implement",
    "in",
    "of",
    "schema",
    "service",
    "the",
    "to",
    "with",
}


def _tokens(value: str) -> list[str]:
    return [match.group(0).lower() for match in _TOKEN_RE.finditer(value)]


def slugify(value: str) -> str:
    """Return a filesystem-friendly slug."""
    tokens = _tokens(value)
    return "-".join(tokens) or "schema"


def snake_case(value: str) -> str:
    """Return an underscore-separated identifier."""
    return slugify(value).replace("-", "_")


def pascal_case(value: str) -> str:
    """Return a PascalCase identifier."""
    tokens = _tokens(value)
    return "".join(token.capitalize() for token in tokens) or "Schema"


def issue_stem(issue: Issue) -> str:
    """Return a compact, deterministic stem derived from the issue title."""
    preferred_tokens = [token for token in _tokens(issue.title) if token not in _STOPWORDS]
    return "-".join(preferred_tokens[:3] or _tokens(issue.title)[:3] or ["schema"])


def issue_summary(issue: Issue) -> str:
    """Return a short single-line summary for generated schemas."""
    source = issue.description.strip() or issue.title.strip()
    for line in source.splitlines():
        cleaned = re.sub(r"\s+", " ", line).strip()
        if cleaned:
            return cleaned
    return issue.title.strip() or "Generated schema"
