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
        resolved = cls._normalize_aliases(resolved)
        hooks = resolved.get("hooks")
        if isinstance(hooks, dict):
            workspace = resolved.get("workspace")
            merged_workspace = dict(workspace) if isinstance(workspace, dict) else {}

            workspace_hooks = merged_workspace.get("hooks")
            merged_hooks = dict(workspace_hooks) if isinstance(workspace_hooks, dict) else {}
            merged_hooks.update(hooks)
            merged_workspace["hooks"] = merged_hooks
            resolved["workspace"] = merged_workspace
        return cls(**resolved)

    @staticmethod
    def _normalize_aliases(raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize Symphony-shaped config aliases into Uptempo's runtime schema."""
        normalized = dict(raw)

        tracker = normalized.get("tracker")
        merged_tracker = dict(tracker) if isinstance(tracker, dict) else {}
        polling = normalized.get("polling")

        if "team_key" not in merged_tracker:
            for key in ("project", "project_slug", "slug"):
                if key in merged_tracker:
                    merged_tracker["team_key"] = merged_tracker[key]
                    break
        if "eligible_states" not in merged_tracker and "active_states" in merged_tracker:
            merged_tracker["eligible_states"] = merged_tracker["active_states"]
        if isinstance(polling, dict) and "poll_interval_ms" not in merged_tracker:
            for key in ("interval_ms", "poll_interval_ms"):
                if key in polling:
                    merged_tracker["poll_interval_ms"] = polling[key]
                    break

        terminal_states = merged_tracker.get("terminal_states")
        if isinstance(terminal_states, dict):
            if "done_state" not in merged_tracker:
                for key in ("done", "success", "completed"):
                    if key in terminal_states:
                        merged_tracker["done_state"] = terminal_states[key]
                        break
            if "error_state" not in merged_tracker:
                for key in ("error", "failure", "failed", "cancelled"):
                    if key in terminal_states:
                        merged_tracker["error_state"] = terminal_states[key]
                        break

        if merged_tracker or isinstance(tracker, dict):
            normalized["tracker"] = merged_tracker

        agent = normalized.get("agent")
        merged_agent = dict(agent) if isinstance(agent, dict) else {}
        codex = normalized.get("codex")
        if isinstance(codex, dict):
            if "codex_cmd" not in merged_agent:
                for key in ("cmd", "command"):
                    if key in codex:
                        merged_agent["codex_cmd"] = codex[key]
                        break
            if "turn_timeout_ms" not in merged_agent:
                for key in ("turn_timeout_ms", "timeout_ms"):
                    if key in codex:
                        merged_agent["turn_timeout_ms"] = codex[key]
                        break
        if merged_agent or isinstance(agent, dict):
            normalized["agent"] = merged_agent

        return normalized

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
