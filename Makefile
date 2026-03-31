.PHONY: all fmt lint test typecheck

all: fmt lint test typecheck

fmt:
	black src/ api/ demo/ tests/
	isort src/ api/ demo/ tests/

lint:
	ruff check src/ api/ demo/ tests/

test:
	pytest tests/ -v

typecheck:
	mypy src/
