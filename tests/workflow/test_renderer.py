from __future__ import annotations

from textwrap import dedent

import pytest

from uptempo.tracker.models import Issue
from uptempo.workflow.renderer import RenderError, WorkflowRenderer


@pytest.fixture()
def renderer() -> WorkflowRenderer:
    return WorkflowRenderer()


@pytest.fixture()
def issue() -> Issue:
    return Issue(
        id="issue-1",
        identifier="UPT-3",
        title="Render workflow templates",
        description="Implement the Liquid renderer.",
    )


class TestWorkflowRenderer:
    def test_render_renders_issue_fields(self, renderer: WorkflowRenderer, issue: Issue) -> None:
        template = dedent(
            """\
            Issue: {{ issue.identifier }}
            Title: {{ issue.title }}
            """
        )

        result = renderer.render(template, {"issue": issue, "attempt": None})

        assert result == "Issue: UPT-3\nTitle: Render workflow templates\n"

    def test_render_omits_attempt_branch_when_attempt_is_none(
        self, renderer: WorkflowRenderer, issue: Issue
    ) -> None:
        template = dedent(
            """\
            Start
            {% if attempt %}
            Retry attempt #{{ attempt }}
            {% endif %}
            Done
            """
        )

        result = renderer.render(template, {"issue": issue, "attempt": None})

        assert "Retry attempt" not in result
        assert result == "Start\n\nDone\n"

    def test_render_includes_attempt_branch_when_attempt_is_present(
        self, renderer: WorkflowRenderer, issue: Issue
    ) -> None:
        template = dedent(
            """\
            Start
            {% if attempt %}
            Retry attempt #{{ attempt }}
            {% endif %}
            Done
            """
        )

        result = renderer.render(template, {"issue": issue, "attempt": 2})

        assert result == "Start\n\nRetry attempt #2\n\nDone\n"

    def test_render_raises_render_error_for_unknown_variable(
        self, renderer: WorkflowRenderer, issue: Issue
    ) -> None:
        with pytest.raises(RenderError, match="undefined"):
            renderer.render("{{ issue.missing_field }}", {"issue": issue, "attempt": None})

    def test_render_raises_render_error_for_unknown_filter(
        self, renderer: WorkflowRenderer, issue: Issue
    ) -> None:
        with pytest.raises(RenderError, match="unknown filter"):
            renderer.render(
                "{{ issue.title | missing_filter }}", {"issue": issue, "attempt": None}
            )
