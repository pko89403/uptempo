from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from uptempo.config.settings import Config
from uptempo.tracker.linear import (
    ADD_COMMENT_MUTATION,
    FETCH_ISSUES_QUERY,
    LINEAR_GRAPHQL_URL,
    UPDATE_ISSUE_STATE_MUTATION,
    LinearAPIError,
    LinearClient,
)
from uptempo.tracker.models import Issue, Label


def make_config(*, team_key: str = "UPT", eligible_states: list[str] | None = None) -> Config:
    return Config.from_frontmatter(
        {
            "tracker": {
                "team_key": team_key,
                "eligible_states": eligible_states or ["In Progress"],
            }
        }
    )


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


class TestIssueParsing:
    def test_issue_from_linear_node(self) -> None:
        node = {
            "id": "issue-1",
            "identifier": "UPT-1",
            "title": "Implement tracker client",
            "description": None,
            "state": {"name": "In Progress"},
            "labels": {"nodes": [{"id": "label-1", "name": "backend"}]},
        }

        issue = Issue.from_linear_node(node)

        assert issue == Issue(
            id="issue-1",
            identifier="UPT-1",
            title="Implement tracker client",
            description="",
            state="In Progress",
            labels=[Label(id="label-1", name="backend")],
        )


class TestLinearClient:
    def test_init_resolves_api_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LINEAR_API_KEY", "linear-token")

        client = LinearClient(make_config())

        assert client._api_key == "linear-token"

    async def test_fetch_issues_returns_filtered_issues(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("LINEAR_API_KEY", "linear-token")
        client = LinearClient(make_config(eligible_states=["In Progress", "Todo"]))

        execute = AsyncMock(
            return_value={
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
        )
        monkeypatch.setattr(client, "_execute", execute)

        issues = await client.fetch_issues()

        execute.assert_awaited_once_with(FETCH_ISSUES_QUERY, {"teamKey": "UPT"})
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

    async def test_update_issue_state_sends_expected_mutation_payload(
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

        assert captured["url"] == LINEAR_GRAPHQL_URL
        assert captured["headers"]["Authorization"] == "linear-token"
        assert captured["json"] == {
            "query": UPDATE_ISSUE_STATE_MUTATION,
            "variables": {"issueId": "issue-1", "stateId": "state-1"},
        }

    async def test_add_comment_sends_expected_mutation_payload(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("LINEAR_API_KEY", "linear-token")
        client = LinearClient(make_config())
        captured: dict[str, Any] = {}
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

        assert captured["url"] == LINEAR_GRAPHQL_URL
        assert captured["headers"]["Authorization"] == "linear-token"
        assert captured["json"] == {
            "query": ADD_COMMENT_MUTATION,
            "variables": {"issueId": "issue-1", "body": "Ship it"},
        }

    async def test_execute_surfaces_http_error_body(
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

        with pytest.raises(
            LinearAPIError,
            match=r"HTTP 400: .*Invalid input",
        ):
            await client._execute("query Example { viewer { id } }")

    async def test_execute_raises_for_graphql_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("LINEAR_API_KEY", "linear-token")
        client = LinearClient(make_config())
        response = httpx.Response(
            200,
            request=httpx.Request("POST", LINEAR_GRAPHQL_URL),
            json={"errors": [{"message": "nope"}]},
        )

        monkeypatch.setattr(
            "uptempo.tracker.linear.httpx.AsyncClient",
            lambda: MockAsyncClient(response=response, captured={}),
        )

        with pytest.raises(LinearAPIError, match="nope"):
            await client._execute("query Example { viewer { id } }")
