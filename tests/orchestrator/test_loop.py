from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock

import pytest

from uptempo.agent.runner import AgentResult
from uptempo.config.settings import Config
from uptempo.orchestrator.dispatcher import Dispatcher
from uptempo.orchestrator.loop import _backoff_delay, _poll_tick
from uptempo.tracker.models import Issue, Label
from uptempo.workflow.loader import WorkflowLoader
from uptempo.workflow.renderer import WorkflowRenderer
from uptempo.workspace.manager import WorkspaceInfo

if TYPE_CHECKING:
    from pathlib import Path


def make_config(tmp_path: Path) -> Config:
    return Config.from_frontmatter(
        {
            "tracker": {
                "team_key": "UPT",
                "eligible_states": ["In Progress"],
                "done_state": "Done",
            },
            "workspace": {"root": str(tmp_path / "workspaces")},
        }
    )


def make_issue() -> Issue:
    return Issue(
        id="issue-1",
        identifier="UPT-1",
        title="Generate schema",
        description="Create a proto file.",
        state="In Progress",
        labels=[Label(id="label-1", name="backend")],
    )


def write_workflow(tmp_path: Path) -> None:
    (tmp_path / "WORKFLOW.md").write_text(
        dedent(
            """\
            ---
            tracker:
              team_key: "UPT"
            ---

            Issue {{ issue.identifier }}
            {% if agent.max_concurrency %}Concurrency {{ agent.max_concurrency }}{% endif %}
            """
        ),
        encoding="utf-8",
    )


class TestBackoffDelay:
    def test_backoff_grows_and_caps(self) -> None:
        assert _backoff_delay(0, 5_000) == 1.0
        assert _backoff_delay(1, 5_000) == 2.0
        assert _backoff_delay(3, 5_000) == 5.0

    def test_backoff_rejects_negative_attempt(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            _backoff_delay(-1, 5_000)


class TestPollTick:
    async def test_poll_tick_success_flow(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        write_workflow(tmp_path)
        config = make_config(tmp_path)
        dispatcher = Dispatcher(config)
        issue = make_issue()
        workspace_path = tmp_path / "workspaces" / issue.id
        artifact_path = workspace_path / "proto" / "service.proto"
        loop_logger = Mock()
        monkeypatch.setattr("uptempo.orchestrator.loop.logger", loop_logger)

        tracker = AsyncMock()
        tracker.fetch_issues.return_value = [issue]

        workspace_mgr = AsyncMock()

        async def create_workspace(issue_id: str) -> WorkspaceInfo:
            artifact_path.parent.mkdir(parents=True)
            artifact_path.write_text('syntax = "proto3";', encoding="utf-8")
            return WorkspaceInfo(issue_id=issue_id, path=workspace_path)

        workspace_mgr.create.side_effect = create_workspace
        agent_runner = AsyncMock()
        agent_runner.run.return_value = AgentResult(
            success=True,
            output="done",
            thread_id="thread-1",
            turn_id="turn-1",
        )

        await _poll_tick(
            config=config,
            tracker=tracker,
            dispatcher=dispatcher,
            workspace_mgr=workspace_mgr,
            agent_runner=agent_runner,
            workflow_loader=WorkflowLoader(),
            workflow_renderer=WorkflowRenderer(),
        )

        tracker.update_issue_state.assert_not_awaited()
        tracker.add_comment.assert_not_awaited()
        workspace_mgr.prepare.assert_awaited_once()
        workspace_mgr.finalise.assert_awaited_once()
        workspace_mgr.remove.assert_awaited_once()
        assert dispatcher._claims == {}
        assert any(
            call.args == ("issue_execution_succeeded",)
            and call.kwargs["issue_id"] == issue.id
            and call.kwargs["report"]["issue_identifier"] == issue.identifier
            and call.kwargs["report"]["generated_artifacts"][0]["path"] == "proto/service.proto"
            for call in loop_logger.info.call_args_list
        )

    async def test_poll_tick_failure_logs_and_releases_claim(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        write_workflow(tmp_path)
        config = make_config(tmp_path)
        dispatcher = Dispatcher(config)
        issue = make_issue()
        workspace_path = tmp_path / "workspaces" / issue.id
        loop_logger = Mock()
        monkeypatch.setattr("uptempo.orchestrator.loop.logger", loop_logger)

        tracker = AsyncMock()
        tracker.fetch_issues.return_value = [issue]

        workspace_mgr = AsyncMock()
        workspace_mgr.create.return_value = WorkspaceInfo(issue_id=issue.id, path=workspace_path)
        agent_runner = AsyncMock()
        agent_runner.run.return_value = AgentResult(
            success=False,
            output="failed",
            thread_id="thread-1",
            turn_id="turn-1",
            error="generation failed",
        )

        await _poll_tick(
            config=config,
            tracker=tracker,
            dispatcher=dispatcher,
            workspace_mgr=workspace_mgr,
            agent_runner=agent_runner,
            workflow_loader=WorkflowLoader(),
            workflow_renderer=WorkflowRenderer(),
        )

        tracker.update_issue_state.assert_not_awaited()
        tracker.add_comment.assert_not_awaited()
        workspace_mgr.finalise.assert_awaited_once()
        workspace_mgr.remove.assert_awaited_once()
        assert dispatcher._claims == {}
        assert any(
            call.args == ("issue_execution_unsuccessful",)
            and call.kwargs["issue_id"] == issue.id
            and call.kwargs["report"]["failure_reason"] == "generation failed"
            for call in loop_logger.warning.call_args_list
        )

    async def test_poll_tick_workspace_failure_logs_and_releases_claim(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        write_workflow(tmp_path)
        config = make_config(tmp_path)
        dispatcher = Dispatcher(config)
        issue = make_issue()
        loop_logger = Mock()
        monkeypatch.setattr("uptempo.orchestrator.loop.logger", loop_logger)

        tracker = AsyncMock()
        tracker.fetch_issues.return_value = [issue]

        workspace_mgr = AsyncMock()
        workspace_mgr.create.side_effect = RuntimeError("hook failed")
        agent_runner = AsyncMock()

        await _poll_tick(
            config=config,
            tracker=tracker,
            dispatcher=dispatcher,
            workspace_mgr=workspace_mgr,
            agent_runner=agent_runner,
            workflow_loader=WorkflowLoader(),
            workflow_renderer=WorkflowRenderer(),
        )

        tracker.update_issue_state.assert_not_awaited()
        tracker.add_comment.assert_not_awaited()
        workspace_mgr.remove.assert_not_awaited()
        assert dispatcher._claims == {}
        assert any(
            call.args == ("issue_execution_failed",)
            and call.kwargs["issue_id"] == issue.id
            and call.kwargs["report"]["failure_reason"] == "hook failed"
            for call in loop_logger.exception.call_args_list
        )
