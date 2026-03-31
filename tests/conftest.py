"""Shared pytest fixtures for the Uptempo test suite."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Generator
from unittest.mock import AsyncMock

import pytest


@pytest.fixture()
def tmp_workspace(tmp_path: Path) -> Path:
    """Provide a disposable workspace directory pre-seeded with scaffold dirs."""
    for subdir in ("schemas", "output", ".uptempo"):
        (tmp_path / subdir).mkdir()
    return tmp_path


@pytest.fixture()
def mock_linear_client() -> AsyncMock:
    """Mock Linear GraphQL API client.

    Patch the real client in tests that exercise tracker integration
    so no network calls are made.
    """
    client = AsyncMock()
    client.execute_query.return_value = {"data": {"issues": {"nodes": []}}}
    return client


@pytest.fixture()
def mock_agent() -> AsyncMock:
    """Mock Codex agent subprocess.

    Stands in for the real agent so orchestrator / workflow tests
    run without spawning subprocesses.
    """
    agent = AsyncMock()
    agent.run.return_value = {"status": "completed", "output": ""}
    return agent


@pytest.fixture()
def sample_schema_path(tmp_workspace: Path) -> Path:
    """Write a minimal .proto fixture and return its path."""
    proto = tmp_workspace / "schemas" / "example.proto"
    proto.write_text(
        'syntax = "proto3";\n'
        "package example;\n\n"
        "service Greeter {\n"
        "  rpc SayHello (HelloRequest) returns (HelloReply);\n"
        "}\n\n"
        "message HelloRequest { string name = 1; }\n"
        "message HelloReply   { string message = 1; }\n"
    )
    return proto


@pytest.fixture()
def snapshot_dir() -> Path:
    """Directory containing golden-file snapshots for schema generation tests."""
    return Path(__file__).parent / "snapshots"
