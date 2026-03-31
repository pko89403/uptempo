---
description: "Enforce pytest patterns, AAA structure, and coverage requirements for tests"
paths:
  - "tests/**/*.py"
excludePaths:
  - "tests/conftest.py"
priority: 5
---

# Test Rules

## Framework & Style

- Use pytest exclusively — never use `unittest` or `self.assert*` methods.
- Follow the AAA pattern: Arrange, Act, Assert — separate each section with a blank line.
- Name test functions as `test_{method}_{scenario}_{expected}` (e.g., `test_generate_with_rest_label_returns_openapi_file`).

## Fixtures & Parametrization

- Use `@pytest.fixture` for reusable setup; place shared fixtures in `conftest.py`.
- Use `pytest.mark.parametrize` for data-driven tests.
- Use the `tmp_path` fixture for file-system tests — never create temp directories manually.

## Assertions & Mocking

- Use `pytest.raises(ExceptionType)` for expected errors.
- Mock external dependencies with `unittest.mock.patch` or `pytest-mock`.

## Imports & Isolation

- Never import from `src/` directly — always import from the package (e.g., `from uptempo.schema import ...`).
- Keep tests fast — no network calls, no disk I/O beyond `tmp_path`.

## File Organization

- Mirror source modules: `tests/schema/test_openapi.py` → `src/uptempo/schema/openapi.py`.
- Run the suite with: `uv run pytest tests/ -v`.
