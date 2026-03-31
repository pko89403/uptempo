"""OpenAPI 3.1 webhook schema generator.

Output is placed in ``<workspace>/webhook/``.  Validation uses `Spectral
<https://github.com/stoplightio/spectral>`_.

The generated spec covers the full subscription lifecycle, HMAC-SHA256
signature verification schema, retry policies, and idempotency keys.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from uptempo.schema.base import SchemaGenerator

if TYPE_CHECKING:
    from pathlib import Path

    from uptempo.tracker.models import Issue

logger = structlog.get_logger(__name__)


class WebhookGenerator(SchemaGenerator):
    """Generate OpenAPI 3.1 YAML with Callbacks for Webhook integrations."""

    def generate(self, issue: Issue, workspace: Path) -> list[Path]:
        """Parse issue for webhook requirements and emit OpenAPI 3.1.

        Extracts event types, callback URLs, and signature schemes from
        the issue and generates an OpenAPI 3.1 specification with
        callbacks and JSON Schema payloads.
        """
        raise NotImplementedError

    def validate(self, files: list[Path]) -> list[str]:
        """Validate webhook schemas with Spectral.

        Verifies signature verification schema presence and callback
        object completeness.
        """
        raise NotImplementedError
