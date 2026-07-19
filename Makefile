.PHONY: dev test lint

dev:
	docker compose up

test:
	cd backend && python3.12 -m pytest

lint:
	cd backend && python3.12 -m ruff check . && python3.12 -m mypy .
