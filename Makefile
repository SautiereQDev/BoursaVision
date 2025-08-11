# Makefile for Boursa Vision Trading Platform
# ========================================

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default variables
DOCKER_COMPOSE_DEV := docker/docker-compose.dev.yml
DOCKER_COMPOSE_PROD := docker/docker-compose.prod.yml
DOCKER_COMPOSE_TEST := docker/docker-compose.test.yml
BACKEND_DIR := backend
FRONTEND_DIR := frontend

# Help target
.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)Boursa Vision - Available Commands$(NC)"
	@echo "=================================="
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ========================================
# Environment Setup
# ========================================

.PHONY: check-python
check-python: ## Check Python version compatibility
	@chmod +x scripts/check-python-version.sh
	@./scripts/check-python-version.sh

.PHONY: setup
setup: ## Initial project setup
	@echo "$(YELLOW)Setting up Boursa Vision environment...$(NC)"
	@chmod +x scripts/check-python-version.sh
	@./scripts/check-python-version.sh
	@if [ ! -f .env ]; then \
		cp .env.template .env && \
		echo "$(GREEN)Created .env file from template$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi
	@$(MAKE) install-backend
	@$(MAKE) install-frontend
	@echo "$(GREEN)Setup complete! Run 'make dev' to start development environment$(NC)"

.PHONY: clean
clean: ## Clean all build artifacts and caches
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@rm -rf $(BACKEND_DIR)/.pytest_cache
	@rm -rf $(BACKEND_DIR)/__pycache__
	@rm -rf $(BACKEND_DIR)/src/**/__pycache__
	@rm -rf $(FRONTEND_DIR)/node_modules
	@rm -rf $(FRONTEND_DIR)/dist
	@rm -rf $(FRONTEND_DIR)/.vite
	@docker system prune -f
	@echo "$(GREEN)Cleanup complete$(NC)"

# ========================================
# Dependencies Installation
# ========================================

.PHONY: install
install: install-backend install-frontend ## Install all dependencies

.PHONY: install-backend
install-backend: ## Install backend dependencies
	@echo "$(YELLOW)Installing backend dependencies...$(NC)"
	@cd $(BACKEND_DIR) && \
		if poetry install; then \
			echo "$(GREEN)Backend dependencies installed$(NC)"; \
		else \
			echo "$(RED)Poetry install failed, trying with pip fallback...$(NC)"; \
			poetry run pip install --upgrade pip setuptools wheel; \
			poetry install --no-cache; \
		fi

.PHONY: install-frontend
install-frontend: ## Install frontend dependencies
	@echo "$(YELLOW)Installing frontend dependencies...$(NC)"
	@cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)Frontend dependencies installed$(NC)"

# ========================================
# Development Environment
# ========================================

.PHONY: dev
dev: ## Start development environment with Docker
	@echo "$(YELLOW)Starting development environment...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)❌ .env file not found! Run 'make setup' first$(NC)"; \
		exit 1; \
	fi
	@export $$(cat .env | grep -v '^#' | xargs) && docker-compose -f $(DOCKER_COMPOSE_DEV) up -d --force-recreate --renew-anon-volumes
	@echo "$(GREEN)Development environment started!$(NC)"
	@echo "$(BLUE)Frontend: http://localhost:3000$(NC)"
	@echo "$(BLUE)Backend API: http://localhost:8000$(NC)"
	@echo "$(BLUE)API Docs: http://localhost:8000/docs$(NC)"

.PHONY: dev-stop
dev-stop: ## Stop development environment
	@echo "$(YELLOW)Stopping development environment...$(NC)"
	@export $$(cat .env | grep -v '^#' | xargs) && docker-compose -f $(DOCKER_COMPOSE_DEV) down
	@echo "$(GREEN)Development environment stopped$(NC)"

.PHONY: dev-logs
dev-logs: ## Show development environment logs
	@export $$(cat .env | grep -v '^#' | xargs) && docker-compose -f $(DOCKER_COMPOSE_DEV) logs -f

.PHONY: dev-build
dev-build: ## Build development Docker images
	@echo "$(YELLOW)Building development images...$(NC)"
	@export $$(cat .env | grep -v '^#' | xargs) && docker-compose -f $(DOCKER_COMPOSE_DEV) build
	@echo "$(GREEN)Development images built$(NC)"

.PHONY: dev-rebuild
dev-rebuild: ## Rebuild and restart development environment
	@$(MAKE) dev-stop
	@$(MAKE) dev-build
	@$(MAKE) dev
	@echo "$(GREEN)Development environment rebuilt and restarted$(NC)"

# ========================================
# Local Development (without Docker)
# ========================================

.PHONY: run-backend
run-backend: ## Run backend locally without Docker
	@echo "$(YELLOW)Starting backend server...$(NC)"
	@cd $(BACKEND_DIR) && poetry run uvicorn src.infrastructure.web.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: run-frontend
run-frontend: ## Run frontend locally without Docker
	@echo "$(YELLOW)Starting frontend server...$(NC)"
	@cd $(FRONTEND_DIR) && npm run dev

.PHONY: run-celery
run-celery: ## Run Celery worker locally
	@echo "$(YELLOW)Starting Celery worker...$(NC)"
	@cd $(BACKEND_DIR) && poetry run celery -A src.infrastructure.tasks.celery_app worker -l info

.PHONY: run-celery-beat
run-celery-beat: ## Run Celery beat scheduler locally
	@echo "$(YELLOW)Starting Celery beat...$(NC)"
	@cd $(BACKEND_DIR) && poetry run celery -A src.infrastructure.tasks.celery_app beat -l info

# ========================================
# Database Management
# ========================================

.PHONY: db-upgrade
db-upgrade: ## Run database migrations inside Docker backend
	@echo "$(YELLOW)Running migrations inside boursa-backend container...$(NC)"
	@docker-compose -f $(DOCKER_COMPOSE_DEV) exec backend poetry run alembic upgrade head
	@echo "$(GREEN)Database migrations completed inside container$(NC)"

.PHONY: db-downgrade
db-downgrade: ## Rollback last database migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	@cd $(BACKEND_DIR) && poetry run alembic downgrade -1
	@echo "$(GREEN)Migration rollback completed$(NC)"

.PHONY: db-revision
db-revision: ## Create new database migration (use MSG="..." to skip prompt)
	@msg="$(MSG)"; \
	if [ -z "$$msg" ]; then \
	  read -p "Migration message: " msg; \
	fi; \
	docker-compose -f $(DOCKER_COMPOSE_DEV) exec backend poetry run alembic revision --autogenerate -m "$$msg" && \
	echo "$(GREEN)New migration created$(NC)"

.PHONY: db-history
db-history: ## Show database migration history
	@cd $(BACKEND_DIR) && poetry run alembic history

.PHONY: db-current
db-current: ## Show current database revision
	@cd $(BACKEND_DIR) && poetry run alembic current

.PHONY: db-reset
db-reset: ## Reset database (development only)
	@echo "$(RED)⚠️  This will delete all data! Are you sure? [y/N]$(NC)" && read ans && [ $${ans:-N} = y ]
	@docker-compose -f $(DOCKER_COMPOSE_DEV) down -v
	@docker-compose -f $(DOCKER_COMPOSE_DEV) up -d postgres redis
	@sleep 5
	@$(MAKE) db-upgrade
	@echo "$(GREEN)Database reset completed$(NC)"

.PHONY: db-seed
db-seed: ## Seed database with sample data
	@echo "$(YELLOW)Seeding database with sample data...$(NC)"
	@cd $(BACKEND_DIR) && poetry run python -c "from src.infrastructure.database.seed import seed_dev_data; seed_dev_data()"
	@echo "$(GREEN)Database seeded$(NC)"

# ========================================
# Testing
# ========================================

.PHONY: test
test: test-backend test-frontend ## Run all tests

.PHONY: test-backend
test-backend: ## Run backend tests
	@echo "$(YELLOW)Running backend tests...$(NC)"
	@cd $(BACKEND_DIR) && poetry run pytest tests/ -v
	@echo "$(GREEN)Backend tests completed$(NC)"

.PHONY: test-backend-cov
test-backend-cov: ## Run backend tests with coverage
	@echo "$(YELLOW)Running backend tests with coverage...$(NC)"
	@cd $(BACKEND_DIR) && poetry run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated at backend/htmlcov/index.html$(NC)"

.PHONY: test-frontend
test-frontend: ## Run frontend tests
	@echo "$(YELLOW)Running frontend tests...$(NC)"
	@cd $(FRONTEND_DIR) && npm run test
	@echo "$(GREEN)Frontend tests completed$(NC)"

.PHONY: test-e2e
test-e2e: ## Run end-to-end tests
	@echo "$(YELLOW)Running E2E tests...$(NC)"
	@cd $(FRONTEND_DIR) && npm run test:e2e
	@echo "$(GREEN)E2E tests completed$(NC)"

.PHONY: test-integration
test-integration: ## Run integration tests with Docker
	@echo "$(YELLOW)Running integration tests...$(NC)"
	@docker-compose -f $(DOCKER_COMPOSE_TEST) up --abort-on-container-exit
	@docker-compose -f $(DOCKER_COMPOSE_TEST) down -v
	@echo "$(GREEN)Integration tests completed$(NC)"

# ========================================
# Code Quality
# ========================================

.PHONY: lint
lint: lint-backend lint-frontend ## Run all linters

.PHONY: lint-backend
lint-backend: ## Run backend linting
	@echo "$(YELLOW)Running backend linting...$(NC)"
	@cd $(BACKEND_DIR) && poetry run black --check src tests
	@cd $(BACKEND_DIR) && poetry run isort --check-only src tests
	@cd $(BACKEND_DIR) && poetry run flake8 src tests
	@cd $(BACKEND_DIR) && poetry run mypy src
	@echo "$(GREEN)Backend linting completed$(NC)"

.PHONY: lint-frontend
lint-frontend: ## Run frontend linting
	@echo "$(YELLOW)Running frontend linting...$(NC)"
	@cd $(FRONTEND_DIR) && npm run lint
	@echo "$(GREEN)Frontend linting completed$(NC)"

.PHONY: format
format: format-backend format-frontend ## Format all code

.PHONY: format-backend
format-backend: ## Format backend code
	@echo "$(YELLOW)Formatting backend code...$(NC)"
	@cd $(BACKEND_DIR) && poetry run black src tests
	@cd $(BACKEND_DIR) && poetry run isort src tests
	@echo "$(GREEN)Backend code formatted$(NC)"

.PHONY: format-frontend
format-frontend: ## Format frontend code
	@echo "$(YELLOW)Formatting frontend code...$(NC)"
	@cd $(FRONTEND_DIR) && npm run format
	@echo "$(GREEN)Frontend code formatted$(NC)"

.PHONY: check
check: lint test ## Run all code quality checks

# ========================================
# Production Deployment
# ========================================

.PHONY: prod-build
prod-build: ## Build production Docker images
	@echo "$(YELLOW)Building production images...$(NC)"
	@docker-compose -f $(DOCKER_COMPOSE_PROD) build
	@echo "$(GREEN)Production images built$(NC)"

.PHONY: prod-up
prod-up: ## Start production environment
	@echo "$(YELLOW)Starting production environment...$(NC)"
	@docker-compose -f $(DOCKER_COMPOSE_PROD) up -d
	@echo "$(GREEN)Production environment started$(NC)"

.PHONY: prod-down
prod-down: ## Stop production environment
	@echo "$(YELLOW)Stopping production environment...$(NC)"
	@docker-compose -f $(DOCKER_COMPOSE_PROD) down
	@echo "$(GREEN)Production environment stopped$(NC)"

.PHONY: prod-logs
prod-logs: ## Show production logs
	@docker-compose -f $(DOCKER_COMPOSE_PROD) logs -f

.PHONY: deploy
deploy: ## Deploy to production using script
	@echo "$(YELLOW)Deploying to production...$(NC)"
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh --production --backup
	@echo "$(GREEN)Deployment completed$(NC)"

# ========================================
# Backup and Maintenance
# ========================================

.PHONY: backup
backup: ## Create database backup
	@echo "$(YELLOW)Creating database backup...$(NC)"
	@chmod +x scripts/backup.sh
	@./scripts/backup.sh
	@echo "$(GREEN)Backup completed$(NC)"

.PHONY: restore
restore: ## Restore database from backup
	@echo "$(RED)⚠️  This will restore from the latest backup! Continue? [y/N]$(NC)" && read ans && [ $${ans:-N} = y ]
	@echo "$(YELLOW)Restoring database...$(NC)"
	@chmod +x scripts/backup.sh
	@./scripts/backup.sh --restore
	@echo "$(GREEN)Restore completed$(NC)"

# ========================================
# Docker Management
# ========================================

.PHONY: docker-clean
docker-clean: ## Clean Docker images and containers
	@echo "$(YELLOW)Cleaning Docker resources...$(NC)"
	@docker system prune -f
	@docker volume prune -f
	@echo "$(GREEN)Docker cleanup completed$(NC)"

.PHONY: docker-logs
docker-logs: ## Show all Docker logs
	@docker-compose -f $(DOCKER_COMPOSE_DEV) logs

.PHONY: docker-ps
docker-ps: ## Show running containers
	@docker-compose -f $(DOCKER_COMPOSE_DEV) ps

.PHONY: docker-exec-backend
docker-exec-backend: ## Execute shell in backend container
	@docker-compose -f $(DOCKER_COMPOSE_DEV) exec backend bash

.PHONY: docker-exec-frontend
docker-exec-frontend: ## Execute shell in frontend container
	@docker-compose -f $(DOCKER_COMPOSE_DEV) exec frontend sh

.PHONY: docker-exec-postgres
docker-exec-postgres: ## Execute psql in PostgreSQL container
	@docker-compose -f $(DOCKER_COMPOSE_DEV) exec postgres psql -U boursa_user -d boursa_vision

# ========================================
# Monitoring and Health Checks
# ========================================

.PHONY: health
health: ## Check health of all services
	@echo "$(YELLOW)Checking service health...$(NC)"
	@curl -f http://localhost:8000/health || echo "$(RED)Backend health check failed$(NC)"
	@curl -f http://localhost:5173 || echo "$(RED)Frontend health check failed$(NC)"
	@echo "$(GREEN)Health checks completed$(NC)"

.PHONY: status
status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose -f $(DOCKER_COMPOSE_DEV) ps

.PHONY: logs-backend
logs-backend: ## Show backend logs
	@docker-compose -f $(DOCKER_COMPOSE_DEV) logs -f backend

.PHONY: logs-frontend
logs-frontend: ## Show frontend logs
	@docker-compose -f $(DOCKER_COMPOSE_DEV) logs -f frontend

.PHONY: logs-postgres
logs-postgres: ## Show PostgreSQL logs
	@docker-compose -f $(DOCKER_COMPOSE_DEV) logs -f postgres

# ========================================
# Documentation
# ========================================

.PHONY: docs
docs: ## Generate and serve documentation
	@echo "$(YELLOW)Generating documentation...$(NC)"
	@echo "$(BLUE)API Documentation: http://localhost:8000/docs$(NC)"
	@echo "$(BLUE)ReDoc: http://localhost:8000/redoc$(NC)"

# ========================================
# Quick Development Workflows
# ========================================

.PHONY: quick-start
quick-start: setup dev ## Quick setup and start development environment
	@echo "$(GREEN)🚀 Boursa Vision is ready for development!$(NC)"
	@echo "$(BLUE)Frontend: http://localhost:5173$(NC)"
	@echo "$(BLUE)Backend: http://localhost:8000$(NC)"
	@echo "$(BLUE)API Docs: http://localhost:8000/docs$(NC)"

.PHONY: full-reset
full-reset: dev-stop docker-clean setup dev ## Complete reset and restart
	@echo "$(GREEN)Full reset completed$(NC)"

.PHONY: ci
ci: lint test ## Run CI pipeline locally
	@echo "$(GREEN)CI pipeline completed successfully$(NC)"

# ========================================
# Default target
# ========================================

.DEFAULT_GOAL := help
