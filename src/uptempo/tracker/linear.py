"""Async Linear GraphQL adapter.

Wraps the Linear API to fetch, filter, and update issues.  All responses
are normalised into ``Issue`` / ``Label`` domain models.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import httpx
import structlog

from uptempo.tracker.models import Issue

if TYPE_CHECKING:
    from uptempo.config.settings import Config

logger = structlog.get_logger(__name__)

LINEAR_GRAPHQL_URL = "https://api.linear.app/graphql"

FETCH_ISSUES_QUERY = """
query FetchIssues($teamKey: String!) {
  issues(filter: { team: { key: { eq: $teamKey } } }) {
    nodes {
      id
      identifier
      title
      description
      team {
        key
      }
      state {
        name
      }
      labels {
        nodes {
          id
          name
        }
      }
    }
  }
}
"""

UPDATE_ISSUE_STATE_MUTATION = """
mutation UpdateIssueState($issueId: String!, $stateId: String!) {
  issueUpdate(id: $issueId, input: { stateId: $stateId }) {
    success
  }
}
"""

ADD_COMMENT_MUTATION = """
mutation AddComment($issueId: String!, $body: String!) {
  commentCreate(input: { issueId: $issueId, body: $body }) {
    success
  }
}
"""


class LinearAPIError(RuntimeError):
    """Raised when Linear returns an HTTP or GraphQL error."""


class LinearClient:
    """Async client for the Linear GraphQL API."""

    _api_key: str
    _team_key: str
    _eligible_states: frozenset[str]

    def __init__(self, config: Config) -> None:
        try:
            self._api_key = os.environ["LINEAR_API_KEY"]
        except KeyError as exc:
            raise KeyError("Environment variable 'LINEAR_API_KEY' is not set") from exc

        self._team_key = config.tracker.team_key
        self._eligible_states = frozenset(config.tracker.eligible_states)

    async def fetch_issues(self) -> list[Issue]:
        """Poll Linear for issues matching configured filters."""
        data = await self._execute(FETCH_ISSUES_QUERY, {"teamKey": self._team_key})
        issue_nodes = data.get("issues", {}).get("nodes", [])
        if not isinstance(issue_nodes, list):
            raise LinearAPIError("Linear response contained invalid issue nodes")

        filtered_nodes = []
        for node in issue_nodes:
            if not isinstance(node, dict):
                continue

            team = node.get("team")
            team_key = team.get("key", "") if isinstance(team, dict) else ""
            state = node.get("state")
            state_name = state.get("name", "") if isinstance(state, dict) else ""

            if team_key != self._team_key:
                continue
            if state_name not in self._eligible_states:
                continue
            filtered_nodes.append(node)

        return [Issue.from_linear_node(node) for node in filtered_nodes]

    async def update_issue_state(self, issue_id: str, state_id: str) -> None:
        """Transition an issue to a new workflow state in Linear."""
        data = await self._execute(
            UPDATE_ISSUE_STATE_MUTATION,
            {"issueId": issue_id, "stateId": state_id},
        )
        success = data.get("issueUpdate", {}).get("success")
        if success is not True:
            raise LinearAPIError("Linear issueUpdate mutation was not successful")

    async def add_comment(self, issue_id: str, body: str) -> None:
        """Post a comment on a Linear issue."""
        data = await self._execute(
            ADD_COMMENT_MUTATION,
            {"issueId": issue_id, "body": body},
        )
        success = data.get("commentCreate", {}).get("success")
        if success is not True:
            raise LinearAPIError("Linear commentCreate mutation was not successful")

    async def _execute(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a GraphQL request and return the JSON response body."""
        payload = {"query": query, "variables": variables or {}}
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    LINEAR_GRAPHQL_URL,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("linear_request_failed")
            raise LinearAPIError("Linear API request failed") from exc

        body = response.json()
        if not isinstance(body, dict):
            raise LinearAPIError("Linear API returned a non-object JSON response")

        errors = body.get("errors")
        if isinstance(errors, list) and errors:
            messages = ", ".join(
                str(error.get("message", "Unknown GraphQL error"))
                for error in errors
                if isinstance(error, dict)
            )
            raise LinearAPIError(messages or "Linear API returned GraphQL errors")

        data = body.get("data")
        if not isinstance(data, dict):
            raise LinearAPIError("Linear API response did not include a data object")
        return data
