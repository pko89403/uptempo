"""OpenAPI 3.1 YAML schema generator.

Output is placed in ``<workspace>/openapi/`` and validated with Spectral.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from uptempo.schema.base import SchemaGenerator

if TYPE_CHECKING:
    from pathlib import Path

    from uptempo.tracker.models import Issue

logger = structlog.get_logger(__name__)


class OpenApiGenerator(SchemaGenerator):
    """Generate OpenAPI 3.1 YAML specifications."""

    def generate(self, issue: Issue, workspace: Path) -> list[Path]:
        raise NotImplementedError

    def validate(self, files: list[Path]) -> list[str]:
        raise NotImplementedError
