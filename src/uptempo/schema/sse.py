"""OpenAPI 3.1 YAML schema generator for Server-Sent Events endpoints.

Output is placed in ``<workspace>/sse/`` and validated with Spectral plus
custom SSE rules that enforce ``text/event-stream`` media types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from uptempo.schema.base import SchemaGenerator

if TYPE_CHECKING:
    from pathlib import Path

    from uptempo.tracker.models import Issue

logger = structlog.get_logger(__name__)


class SseGenerator(SchemaGenerator):
    """Generate OpenAPI 3.1 YAML with text/event-stream media type for SSE endpoints."""

    def generate(self, issue: Issue, workspace: Path) -> list[Path]:
        """Parse issue for SSE endpoint requirements (event types, reconnection, keep-alive) and generate OpenAPI 3.1 with text/event-stream responses."""
        raise NotImplementedError

    def validate(self, files: list[Path]) -> list[str]:
        """Validate SSE schemas with Spectral and verify EventSource-compatible event type definitions."""
        raise NotImplementedError
