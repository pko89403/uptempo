from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from uptempo.config.settings import AgentConfig, Config, TrackerConfig, WorkspaceConfig


class TestFromFrontmatter:
    def test_from_frontmatter_minimal(self):
        raw = {"tracker": {"team_key": "UPT"}}
        cfg = Config.from_frontmatter(raw)

        assert cfg.tracker.team_key == "UPT"
        assert cfg.tracker.poll_interval_ms == 10_000
        assert cfg.tracker.labels_include == []
        assert cfg.tracker.labels_exclude == []
        assert cfg.tracker.eligible_states == ["In Progress"]
        assert cfg.tracker.done_state == "Done"
        assert cfg.tracker.error_state == "Cancelled"
        assert cfg.agent == AgentConfig()
        assert cfg.workspace == WorkspaceConfig()

    def test_from_frontmatter_full(self):
        raw = {
            "tracker": {
                "team_key": "PROJ",
                "poll_interval_ms": 5000,
                "labels_include": ["bug", "feature"],
                "labels_exclude": ["wontfix"],
                "eligible_states": ["Todo", "In Progress"],
                "done_state": "Closed",
                "error_state": "Error",
            },
            "agent": {
                "model": "gpt-4o",
                "temperature": 0.7,
                "max_concurrency": 4,
                "max_retry_backoff_ms": 30_000,
                "codex_cmd": "/usr/local/bin/codex",
            },
            "workspace": {
                "root": "/opt/workspaces",
                "hooks": {"pre_push": "lint.sh", "post_merge": "deploy.sh"},
            },
        }
        cfg = Config.from_frontmatter(raw)

        assert cfg.tracker.team_key == "PROJ"
        assert cfg.tracker.poll_interval_ms == 5000
        assert cfg.tracker.labels_include == ["bug", "feature"]
        assert cfg.tracker.labels_exclude == ["wontfix"]
        assert cfg.tracker.eligible_states == ["Todo", "In Progress"]
        assert cfg.tracker.done_state == "Closed"
        assert cfg.tracker.error_state == "Error"

        assert cfg.agent.model == "gpt-4o"
        assert cfg.agent.temperature == 0.7
        assert cfg.agent.max_concurrency == 4
        assert cfg.agent.max_retry_backoff_ms == 30_000
        assert cfg.agent.codex_cmd == "/usr/local/bin/codex"

        assert cfg.workspace.root == Path("/opt/workspaces")
        assert cfg.workspace.hooks == {"pre_push": "lint.sh", "post_merge": "deploy.sh"}

    def test_from_frontmatter_with_workflow_md_data(self):
        raw = {
            "tracker": {
                "team_key": "UPT",
                "poll_interval_ms": 10000,
                "labels_include": ["uptempo"],
                "labels_exclude": ["blocked"],
                "eligible_states": ["In Progress"],
                "done_state": "Done",
                "error_state": "Cancelled",
            },
            "agent": {
                "model": "gpt-4o",
                "temperature": 0.0,
                "max_concurrency": 2,
                "max_retry_backoff_ms": 60000,
                "codex_cmd": "codex",
            },
            "workspace": {
                "root": "./workspaces",
                "hooks": {"pre_push": "scripts/lint.sh"},
            },
        }
        cfg = Config.from_frontmatter(raw)

        assert cfg.tracker.team_key == "UPT"
        assert cfg.tracker.labels_include == ["uptempo"]
        assert cfg.agent.model == "gpt-4o"
        assert cfg.agent.max_concurrency == 2
        assert cfg.workspace.root == Path("./workspaces")
        assert cfg.workspace.hooks == {"pre_push": "scripts/lint.sh"}

    def test_from_frontmatter_merges_top_level_hooks_into_workspace_hooks(self):
        raw = {
            "tracker": {"team_key": "UPT"},
            "workspace": {"root": "./workspaces"},
            "hooks": {
                "after_create": "git clone .",
                "before_run": "mise exec -- true",
            },
        }

        cfg = Config.from_frontmatter(raw)

        assert cfg.workspace.root == Path("./workspaces")
        assert cfg.workspace.hooks == {
            "after_create": "git clone .",
            "before_run": "mise exec -- true",
        }

    def test_from_frontmatter_missing_required(self):
        with pytest.raises(ValidationError):
            Config.from_frontmatter({})

        with pytest.raises(ValidationError):
            Config.from_frontmatter({"agent": {"model": "gpt-4o"}})


class TestResolveEnv:
    def test_resolve_env_string(self, monkeypatch):
        monkeypatch.setenv("MY_VAR", "resolved_value")
        assert Config._resolve_env("$MY_VAR") == "resolved_value"

    def test_resolve_env_nested_dict(self, monkeypatch):
        monkeypatch.setenv("TK", "TEAM-42")
        raw = {"tracker": {"team_key": "$TK"}}
        result = Config._resolve_env(raw)
        assert result == {"tracker": {"team_key": "TEAM-42"}}

    def test_resolve_env_list(self, monkeypatch):
        monkeypatch.setenv("A", "alpha")
        monkeypatch.setenv("B", "beta")
        assert Config._resolve_env(["$A", "$B"]) == ["alpha", "beta"]

    def test_resolve_env_missing_var(self, monkeypatch):
        monkeypatch.delenv("NONEXISTENT", raising=False)
        with pytest.raises(KeyError, match="NONEXISTENT"):
            Config._resolve_env("$NONEXISTENT")

    def test_resolve_env_passthrough(self):
        assert Config._resolve_env("plain_string") == "plain_string"
        assert Config._resolve_env(42) == 42
        assert Config._resolve_env(True) is True
        assert Config._resolve_env(3.14) == 3.14
        assert Config._resolve_env(None) is None


class TestDefaults:
    def test_defaults_applied(self):
        agent = AgentConfig()
        assert agent.model == "o4-mini"
        assert agent.temperature == 0.0
        assert agent.max_concurrency == 1
        assert agent.max_retry_backoff_ms == 60_000
        assert agent.codex_cmd == "codex"

        tracker = TrackerConfig(team_key="X")
        assert tracker.poll_interval_ms == 10_000
        assert tracker.labels_include == []
        assert tracker.labels_exclude == []
        assert tracker.eligible_states == ["In Progress"]
        assert tracker.done_state == "Done"
        assert tracker.error_state == "Cancelled"

        ws = WorkspaceConfig()
        assert ws.root == Path("workspaces")
        assert ws.hooks == {}
