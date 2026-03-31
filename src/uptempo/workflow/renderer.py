"""Liquid-compatible template rendering for WORKFLOW.md prompt bodies.

Template variables:
  - ``issue``   — normalised issue fields (id, identifier, title, …)
  - ``attempt`` — ``None`` on first run, integer on retries / continuations
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import structlog
from liquid import Environment, StrictUndefined
from liquid.exceptions import Error, NoSuchFilterFunc, UndefinedError
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class WorkflowRenderer:
    """Render a Liquid template string with contextual variables."""

    def __init__(self) -> None:
        self._environment = Environment(undefined=StrictUndefined, strict_filters=True)

    def render(self, template: str, context: dict[str, Any]) -> str:
        """Return the rendered prompt string.

        Raises ``RenderError`` if the template references unknown variables or filters.
        """
        normalized_context = self._normalize_context(context)

        try:
            bound_template = self._environment.from_string(template)
            rendered = bound_template.render(**normalized_context)
        except UndefinedError as exc:
            logger.warning("workflow_render_failed", error=str(exc))
            raise RenderError(f"undefined variable: {exc}") from exc
        except NoSuchFilterFunc as exc:
            logger.warning("workflow_render_failed", error=str(exc))
            raise RenderError(f"unknown filter: {exc}") from exc
        except Error as exc:
            logger.warning("workflow_render_failed", error=str(exc))
            raise RenderError(str(exc)) from exc

        logger.debug("workflow_rendered", context_keys=list(normalized_context))
        return rendered

    @classmethod
    def _normalize_context(cls, context: dict[str, Any]) -> dict[str, object]:
        return {key: cls._normalize_value(value) for key, value in context.items()}

    @classmethod
    def _normalize_value(cls, value: Any) -> object:
        if isinstance(value, BaseModel):
            return cls._normalize_value(value.model_dump(mode="python"))

        if isinstance(value, Mapping):
            return {str(key): cls._normalize_value(item) for key, item in value.items()}

        if isinstance(value, list):
            return [cls._normalize_value(item) for item in value]

        if isinstance(value, tuple):
            return tuple(cls._normalize_value(item) for item in value)

        return value


class RenderError(Exception):
    """Raised when template rendering fails (unknown variable / filter)."""
