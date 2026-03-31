"""tRPC router and Zod schema generator.

Output is placed in ``<workspace>/trpc/`` and includes router
definitions, Zod schemas, and middleware modules.  Validation uses
``tsc --noEmit``.

.. note::

   Unlike other generators that produce YAML, proto, or GraphQL, this
   generator produces TypeScript files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from uptempo.schema.base import SchemaGenerator

if TYPE_CHECKING:
    from pathlib import Path

    from uptempo.tracker.models import Issue

logger = structlog.get_logger(__name__)


class TrpcGenerator(SchemaGenerator):
    """Generate tRPC router definitions and Zod schemas in TypeScript."""

    def generate(self, issue: Issue, workspace: Path) -> list[Path]:
        """Parse issue for tRPC requirements and emit TypeScript.

        Extracts procedures, queries, mutations, and subscriptions from
        the issue and generates TypeScript router definitions with Zod
        input/output schemas and middleware chains.
        """
        raise NotImplementedError

    def validate(self, files: list[Path]) -> list[str]:
        """Validate generated TypeScript files with ``tsc --noEmit``.

        Checks for type correctness and verifies no ``any`` type leaks.
        """
        raise NotImplementedError
