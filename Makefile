.PHONY: test test-coverage typecheck

test:
	pytest

test-coverage:
	pytest --cov=app --cov-report=term --cov-report=term-missing --cov-fail-under=90

typecheck:
	mypy app
