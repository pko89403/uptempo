from __future__ import annotations

from textwrap import dedent
from typing import Any
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from uptempo.agent.runner import AgentResult
from uptempo.config.settings import Config
from uptempo.orchestrator.dispatcher import Dispatcher
from uptempo.orchestrator.loop import _poll_tick
from uptempo.tracker.linear import (
    ADD_COMMENT_MUTATION,
    FETCH_ISSUES_QUERY,
    LINEAR_GRAPHQL_URL,
    UPDATE_ISSUE_STATE_MUTATION,
    LinearAPIError,
    LinearClient,
)
from uptempo.tracker.models import Issue, Label
from uptempo.workflow.loader import WorkflowLoader
from uptempo.workflow.renderer import WorkflowRenderer
from uptempo.workflow.runtime import WORKFLOW_OVERRIDE_ENV
from uptempo.workspace.manager import WorkspaceInfo


def make_config(*, team_key: str = "UPT", eligible_states: list[str] | None = None) -> Config:
    return Config.from_frontmatter(
        {
            "tracker": {
                "team_key": team_key,
                "eligible_states": eligible_states or ["In Progress"],
            },
            "workspace": {"root": "./workspaces"},
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


def write_workflow(tmp_path) -> str:
    workflow_path = tmp_path / "WORKFLOW.md"
    workflow_path.write_text(
        dedent(
            """\
            ---
            tracker:
              team_key: "UPT"
            workspace:
              root: "./workspaces"
            ---

            Issue {{ issue.identifier }}
            """
        ),
        encoding="utf-8",
    )
    return str(workflow_path)


class MockAsyncClient:
    def __init__(
        self,
        *,
        response: httpx.Response,
        captured: dict[str, Any],
    ) -> None:
        self._response = response
        self._captured = captured

    async def __aenter__(self) -> MockAsyncClient:
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    async def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
    ) -> httpx.Response:
        self._captured["url"] = url
        self._captured["headers"] = headers
        self._captured["json"] = json
        return self._response


class TestLinearIntegrationSuite:
    async def test_fetch_issues_filters_by_team_and_state_through_http_layer(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("LINEAR_API_KEY", "linear-token")
        client = LinearClient(make_config(eligible_states=["In Progress", "Todo"]))
        captured: dict[str, Any] = {}
        response = httpx.Response(
            200,
            request=httpx.Request("POST", LINEAR_GRAPHQL_URL),
            json={
                "data": {
                    "issues": {
                        "nodes": [
                            {
                                "id": "issue-1",
                                "identifier": "UPT-1",
                                "title": "Keep me",
                                "description": "eligible",
                                "team": {"key": "UPT"},
                                "state": {"name": "In Progress"},
                                "labels": {"nodes": []},
                            },
                            {
                                "id": "issue-2",
                                "identifier": "UPT-2",
                                "title": "Wrong state",
                                "description": "",
                                "team": {"key": "UPT"},
                                "state": {"name": "Done"},
                                "labels": {"nodes": []},
                            },
                            {
                                "id": "issue-3",
                                "identifier": "OPS-1",
                                "title": "Wrong team",
                                "description": "",
                                "team": {"key": "OPS"},
                                "state": {"name": "Todo"},
                                "labels": {"nodes": []},
                            },
                        ]
                    }
                }
            },
        )

        monkeypatch.setattr(
            "uptempo.tracker.linear.httpx.AsyncClient",
            lambda: MockAsyncClient(response=response, captured=captured),
        )

        issues = await client.fetch_issues()

        assert issues == [
            Issue(
                id="issue-1",
                identifier="UPT-1",
                title="Keep me",
                description="eligible",
                state="In Progress",
                labels=[],
            )
        ]
        assert captured["url"] == LINEAR_GRAPHQL_URL
        assert captured["headers"]["Authorization"] == "linear-token"
        assert captured["json"] == {"query": FETCH_ISSUES_QUERY, "variables": {"teamKey": "UPT"}}

    async def test_mutation_requests_preserve_linear_auth_contract(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("LINEAR_API_KEY", "linear-token")
        client = LinearClient(make_config())
        captured: dict[str, Any] = {}
        response = httpx.Response(
            200,
            request=httpx.Request("POST", LINEAR_GRAPHQL_URL),
            json={"data": {"issueUpdate": {"success": True}}},
        )

        monkeypatch.setattr(
            "uptempo.tracker.linear.httpx.AsyncClient",
            lambda: MockAsyncClient(response=response, captured=captured),
        )

        await client.update_issue_state("issue-1", "state-1")

        assert captured["headers"]["Authorization"] == "linear-token"
        assert captured["json"] == {
            "query": UPDATE_ISSUE_STATE_MUTATION,
            "variables": {"issueId": "issue-1", "stateId": "state-1"},
        }

        response = httpx.Response(
            200,
            request=httpx.Request("POST", LINEAR_GRAPHQL_URL),
            json={"data": {"commentCreate": {"success": True}}},
        )
        monkeypatch.setattr(
            "uptempo.tracker.linear.httpx.AsyncClient",
            lambda: MockAsyncClient(response=response, captured=captured),
        )

        await client.add_comment("issue-1", "Ship it")

        assert captured["json"] == {
            "query": ADD_COMMENT_MUTATION,
            "variables": {"issueId": "issue-1", "body": "Ship it"},
        }

    async def test_http_errors_surface_linear_response_body(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("LINEAR_API_KEY", "linear-token")
        client = LinearClient(make_config())
        response = httpx.Response(
            400,
            request=httpx.Request("POST", LINEAR_GRAPHQL_URL),
            text='{"errors":[{"message":"Invalid input"}]}',
        )

        monkeypatch.setattr(
            "uptempo.tracker.linear.httpx.AsyncClient",
            lambda: MockAsyncClient(response=response, captured={}),
        )

        with pytest.raises(LinearAPIError, match=r"HTTP 400: .*Invalid input"):
            await client._execute("query Example { viewer { id } }")

    async def test_poll_tick_treats_linear_as_read_only_boundary(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(WORKFLOW_OVERRIDE_ENV, write_workflow(tmp_path))
        config = make_config()
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
        workspace_mgr.remove.assert_not_awaited()
        assert any(
            call.args == ("issue_execution_succeeded",) and call.kwargs["issue_id"] == issue.id
            for call in loop_logger.info.call_args_list
        )
