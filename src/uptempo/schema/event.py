"""AsyncAPI 3.0 schema generator with broker-specific bindings.

Output is placed in ``<workspace>/events/`` for AsyncAPI YAML and
``<workspace>/events/schemas/`` for Avro/JSON Schema payloads.  Validated
with ``asyncapi validate``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from uptempo.schema.base import SchemaGenerator

if TYPE_CHECKING:
    from pathlib import Path

    from uptempo.tracker.models import Issue

logger = structlog.get_logger(__name__)


class EventSchemaGenerator(SchemaGenerator):
    """Generate AsyncAPI 3.0 specifications with broker-specific bindings for Kafka, RabbitMQ, and NATS."""

    def generate(self, issue: Issue, workspace: Path) -> list[Path]:
        """Parse issue for event streaming requirements (topics, exchanges, subjects) and generate AsyncAPI 3.0 with CloudEvents envelope and broker bindings."""
        raise NotImplementedError

    def validate(self, files: list[Path]) -> list[str]:
        """Validate AsyncAPI specs and payload schemas (Avro/JSON Schema) for compatibility and evolution rules."""
        raise NotImplementedError
