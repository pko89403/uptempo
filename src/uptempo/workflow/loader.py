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

import frontmatter
import structlog
import yaml

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
        if not path.exists():
            raise FileNotFoundError(path)

        raw = path.read_text(encoding="utf-8")
        yaml_str, body = self._split_frontmatter(raw)
        config: dict[str, Any] = yaml.safe_load(yaml_str) or {}
        logger.debug("workflow_loaded", path=str(path), config_keys=list(config))
        return WorkflowDefinition(config=config, template=body)

    @staticmethod
    def _split_frontmatter(raw: str) -> tuple[str, str]:
        """Return (yaml_str, template_body) from raw WORKFLOW.md content."""
        stripped = raw.strip()
        if not stripped.startswith("---"):
            raise ValueError("File has no valid YAML frontmatter (missing '---' delimiters)")

        post = frontmatter.parse(raw)
        metadata: dict[str, Any] = post[0]
        body: str = post[1]

        yaml_str = yaml.dump(metadata, default_flow_style=False) if metadata else ""
        return yaml_str, body
