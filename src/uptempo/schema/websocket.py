"""AsyncAPI 3.0 YAML / JSON Schema generator for WebSocket protocols.

Output is placed in ``<workspace>/websocket/``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from uptempo.schema.base import SchemaGenerator

if TYPE_CHECKING:
    from pathlib import Path

    from uptempo.tracker.models import Issue

logger = structlog.get_logger(__name__)


class WebSocketGenerator(SchemaGenerator):
    """Generate AsyncAPI 3.0 YAML or JSON Schema files."""

    def generate(self, issue: Issue, workspace: Path) -> list[Path]:
        raise NotImplementedError

    def validate(self, files: list[Path]) -> list[str]:
        raise NotImplementedError
