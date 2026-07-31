.PHONY: test test-coverage

test:
	pytest

test-coverage:
	pytest --cov=app --cov-report=term --cov-report=term-missing --cov-fail-under=90
