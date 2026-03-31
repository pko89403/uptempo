"""Parse WORKFLOW.md into configuration (YAML frontmatter) and prompt template body.

Expected format::

    ---
    key: value
    ...
    ---
    Liquid template body referencing {{ issue.title }}, {% if attempt %}, etc.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from pathlib import Path

logger = structlog.get_logger(__name__)


class WorkflowDefinition:
    """Parsed representation of a WORKFLOW.md file."""

    config: dict[str, Any]
    template: str

    def __init__(self, config: dict[str, Any], template: str) -> None:
        self.config = config
        self.template = template


class WorkflowLoader:
    """Load and parse WORKFLOW.md files."""

    def load(self, path: Path) -> WorkflowDefinition:
        """Read *path*, split YAML frontmatter from template body."""
        raise NotImplementedError

    @staticmethod
    def _split_frontmatter(raw: str) -> tuple[str, str]:
        """Return (yaml_str, template_body) from raw WORKFLOW.md content."""
        raise NotImplementedError
