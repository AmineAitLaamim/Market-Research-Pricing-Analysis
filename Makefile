.PHONY: run test migrate lint up down build logs restart-frontend

# Local Development (Non-Docker)
run:
	cd backend && uv run python manage.py runserver 0.0.0.0:8000

test:
	uv run --project backend pytest tests/ -v --cov=backend --cov-report=term-missing

migrate:
	cd backend && uv run python manage.py migrate

lint:
	cd backend && uv run flake8 .
	cd backend && uv run black --check .
	cd backend && uv run isort --check-only .

# Docker Commands
up:
	docker compose -f docker/docker-compose.yml up -d

down:
	docker compose -f docker/docker-compose.yml down

build:
	docker compose -f docker/docker-compose.yml up --build -d

logs:
	docker compose -f docker/docker-compose.yml logs -f

restart-frontend:
	docker compose -f docker/docker-compose.yml stop frontend
	docker compose -f docker/docker-compose.yml up -d frontend
