"""GraphQL SDL schema generator.

Output is placed in ``<workspace>/graphql/`` and validated with graphql-js.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from uptempo.schema.base import SchemaGenerator

if TYPE_CHECKING:
    from pathlib import Path

    from uptempo.tracker.models import Issue

logger = structlog.get_logger(__name__)


class GraphQlGenerator(SchemaGenerator):
    """Generate GraphQL SDL schema files."""

    def generate(self, issue: Issue, workspace: Path) -> list[Path]:
        """Parse issue for GraphQL type requirements (queries, mutations, subscriptions, types) and generate SDL with Relay connection spec pagination."""
        raise NotImplementedError

    def validate(self, files: list[Path]) -> list[str]:
        """Validate GraphQL SDL schemas with graphql-js validate for type resolution and directive usage."""
        raise NotImplementedError
