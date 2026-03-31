"""Typed Config class built from WORKFLOW.md YAML frontmatter.

Supports ``$ENV`` interpolation and default values.  All runtime settings
are accessed through this class rather than reading environment variables
directly.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class TrackerConfig(BaseModel):
    team_key: str
    poll_interval_ms: int = 10_000
    labels_include: list[str] = Field(default_factory=list)
    labels_exclude: list[str] = Field(default_factory=list)
    eligible_states: list[str] = Field(default_factory=lambda: ["In Progress"])
    done_state: str = "Done"
    error_state: str = "Cancelled"


class AgentConfig(BaseModel):
    model: str = "o4-mini"
    temperature: float = 0.0
    max_concurrency: int = 1
    max_retry_backoff_ms: int = 60_000
    turn_timeout_ms: int = 300_000
    codex_cmd: str = "codex"


class WorkspaceConfig(BaseModel):
    root: Path = Path("workspaces")
    hooks: dict[str, str] = Field(default_factory=dict)


class Config(BaseModel):
    """Top-level runtime configuration."""

    tracker: TrackerConfig
    agent: AgentConfig = Field(default_factory=AgentConfig)
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)

    @classmethod
    def from_frontmatter(cls, raw: dict[str, Any]) -> Config:
        """Build a ``Config`` from the parsed YAML frontmatter dict.

        Resolves ``$ENV`` references against ``os.environ`` before validation.
        """
        resolved = cls._resolve_env(raw)
        return cls(**resolved)

    @staticmethod
    def _resolve_env(value: Any) -> Any:
        """Recursively replace ``$ENV_VAR`` strings with their values."""
        if isinstance(value, str):
            if value.startswith("$"):
                env_key = value[1:]
                logger.debug("resolving_env_var", key=env_key)
                if env_key not in os.environ:
                    raise KeyError(
                        f"Environment variable '{env_key}' is not set "
                        f"(referenced as '{value}')"
                    )
                return os.environ[env_key]
            return value
        if isinstance(value, dict):
            return {k: Config._resolve_env(v) for k, v in value.items()}
        if isinstance(value, list):
            return [Config._resolve_env(item) for item in value]
        return value
