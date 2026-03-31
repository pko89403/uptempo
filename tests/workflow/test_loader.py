from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

import pytest

from uptempo.workflow.loader import WorkflowDefinition, WorkflowLoader

if TYPE_CHECKING:
    from pathlib import Path

VALID_WORKFLOW = dedent(
    """\
    ---
    agent:
      model: "gpt-4o"
      temperature: 0.2
      max_concurrency: 4

    tracker:
      team_key: "UPT"
      poll_interval_ms: 10000
      eligible_states: ["In Progress"]
      done_state: "Done"

    workspace:
      root: "./workspaces"
    hooks:
      after_create: |
        git clone git@github.com:your-org/your-repo.git .
    ---

    # Schema Generation Task

    You are a network schema generator.

    - **ID**: {{ issue.identifier }}
    - **Title**: {{ issue.title }}

    {% if attempt %}
    Retry attempt #{{ attempt }}.
    {% endif %}
"""
)


@pytest.fixture()
def loader() -> WorkflowLoader:
    return WorkflowLoader()


class TestLoad:
    def test_load_valid_workflow(self, loader: WorkflowLoader, tmp_path: Path) -> None:
        wf_path = tmp_path / "WORKFLOW.md"
        wf_path.write_text(VALID_WORKFLOW, encoding="utf-8")

        result = loader.load(wf_path)

        assert isinstance(result, WorkflowDefinition)
        assert "agent" in result.config
        assert "tracker" in result.config
        assert "workspace" in result.config
        assert "Schema Generation Task" in result.template
        assert "{{ issue.identifier }}" in result.template

    def test_load_extracts_nested_config(self, loader: WorkflowLoader, tmp_path: Path) -> None:
        wf_path = tmp_path / "WORKFLOW.md"
        wf_path.write_text(VALID_WORKFLOW, encoding="utf-8")

        result = loader.load(wf_path)

        assert result.config["tracker"]["team_key"] == "UPT"
        assert result.config["agent"]["model"] == "gpt-4o"
        assert result.config["agent"]["temperature"] == 0.2
        assert "workspace" in result.config
        assert result.config["hooks"]["after_create"].startswith("git clone")

    def test_load_file_not_found(self, loader: WorkflowLoader, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            loader.load(tmp_path / "does_not_exist.md")

    def test_load_no_frontmatter(self, loader: WorkflowLoader, tmp_path: Path) -> None:
        wf_path = tmp_path / "WORKFLOW.md"
        wf_path.write_text("Just plain text, no delimiters.", encoding="utf-8")

        with pytest.raises(ValueError, match="frontmatter"):
            loader.load(wf_path)

    def test_load_empty_frontmatter(self, loader: WorkflowLoader, tmp_path: Path) -> None:
        wf_path = tmp_path / "WORKFLOW.md"
        wf_path.write_text("---\n---\nBody only.\n", encoding="utf-8")

        result = loader.load(wf_path)

        assert result.config == {}
        assert "Body only." in result.template


class TestSplitFrontmatter:
    def test_split_frontmatter_valid(self) -> None:
        raw = "---\nfoo: bar\n---\nHello world"
        yaml_str, body = WorkflowLoader._split_frontmatter(raw)

        assert "foo" in yaml_str
        assert "bar" in yaml_str
        assert "Hello world" in body

    def test_split_frontmatter_no_delimiters(self) -> None:
        with pytest.raises(ValueError, match="frontmatter"):
            WorkflowLoader._split_frontmatter("No delimiters here")
