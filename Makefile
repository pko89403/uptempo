.PHONY: all fmt lint test typecheck

all: fmt lint test typecheck

fmt:
	black src/ tests/
	isort src/ tests/

lint:
	ruff check src/ tests/

test:
	pytest tests/ -v

typecheck:
	mypy src/
