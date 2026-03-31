"""Liquid-compatible template rendering for WORKFLOW.md prompt bodies.

Template variables:
  - ``issue``   — normalised issue fields (id, identifier, title, …)
  - ``attempt`` — ``None`` on first run, integer on retries / continuations
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class WorkflowRenderer:
    """Render a Liquid template string with contextual variables."""

    def render(self, template: str, context: dict[str, Any]) -> str:
        """Return the rendered prompt string.

        Raises ``RenderError`` if the template references unknown variables or filters.
        """
        raise NotImplementedError


class RenderError(Exception):
    """Raised when template rendering fails (unknown variable / filter)."""
