"""Protobuf (proto3) schema generator.

Output is placed in ``<workspace>/proto/`` and validated with ``buf lint``.
Language-specific options (``go_package``, ``java_package``) are included
when the issue specifies a target language.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from uptempo.schema.base import SchemaGenerator

if TYPE_CHECKING:
    from pathlib import Path

    from uptempo.tracker.models import Issue

logger = structlog.get_logger(__name__)


class ProtoGenerator(SchemaGenerator):
    """Generate proto3 ``.proto`` files."""

    def generate(self, issue: Issue, workspace: Path) -> list[Path]:
        raise NotImplementedError

    def validate(self, files: list[Path]) -> list[str]:
        raise NotImplementedError
