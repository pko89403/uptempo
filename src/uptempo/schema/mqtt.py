"""AsyncAPI 3.0 MQTT schema generator.

Output is placed in ``<workspace>/mqtt/``.  Validation uses
``asyncapi validate``.

The generated spec covers topic hierarchies, QoS levels, retained
messages, Last Will and Testament (LWT), and MQTT 5 properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from uptempo.schema.base import SchemaGenerator

if TYPE_CHECKING:
    from pathlib import Path

    from uptempo.tracker.models import Issue

logger = structlog.get_logger(__name__)


class MqttGenerator(SchemaGenerator):
    """Generate AsyncAPI 3.0 YAML with MQTT protocol bindings."""

    def generate(self, issue: Issue, workspace: Path) -> list[Path]:
        """Parse issue for MQTT requirements and emit AsyncAPI 3.0.

        Extracts device types, telemetry, and commands from the issue
        and generates an AsyncAPI 3.0 specification with MQTT bindings,
        topic hierarchies, and QoS annotations.
        """
        raise NotImplementedError

    def validate(self, files: list[Path]) -> list[str]:
        """Validate MQTT AsyncAPI specs.

        Checks channel binding completeness, QoS level annotation, and
        topic hierarchy consistency.
        """
        raise NotImplementedError
