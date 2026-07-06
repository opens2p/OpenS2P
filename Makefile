.PHONY: install dev test lint docker-up docker-build reset-db seed help

APP_VERSION := $(shell cat VERSION 2>/dev/null || echo "0.1.0")

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev: ## Start both backend and frontend dev servers
	@echo "Starting OpenS2P v$(APP_VERSION) development environment..."
	@echo ""
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo ""
	cd backend && uvicorn app.main:app --reload --port 8000 &
	cd frontend && npm run dev

test: ## Run all tests
	cd backend && pytest ../tests/ -v

lint: ## Lint backend code
	cd backend && pip install -q ruff && ruff check app/ && echo "✅ Backend lint passed"

docker-up: ## Start full stack with Docker Compose
	docker compose up --build -d
	@echo "OpenS2P v$(APP_VERSION) running at http://localhost:80"

docker-down: ## Stop Docker Compose stack
	docker compose down

reset-db: ## Drop, recreate, migrate, and seed the database
	@echo "Resetting database..."
	psql -U opens2p -d postgres -c "DROP DATABASE IF EXISTS opens2p_dev" 2>/dev/null || true
	psql -U opens2p -d postgres -c "CREATE DATABASE opens2p_dev" 2>/dev/null || true
	cd backend && alembic upgrade head
	cd backend && python -m app.db.seed
	@echo "✅ Database reset complete"

seed: ## Re-run seed data
	cd backend && python -m app.db.seed

migrate: ## Run pending migrations
	cd backend && alembic upgrade head

migration: ## Create a new migration (usage: make migration msg="description")
	cd backend && alembic revision --autogenerate -m "$(msg)"

version: ## Show application version
	@echo "OpenS2P v$$(cat VERSION 2>/dev/null || echo '0.1.0')"
