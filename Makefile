.PHONY: test test-coverage typecheck docker-build docker-up docker-down

test:
	pytest

test-coverage:
	pytest --cov=app --cov-report=term --cov-report=term-missing --cov-fail-under=90

typecheck:
	mypy app

docker-build:
	docker build -t car-faults-ai-api .

docker-up:
	docker compose down && docker compose up -d --build

docker-down:
	docker compose down
