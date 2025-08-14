# Boursa Vision - Production API with Real YFinance Data
# ======================================================
# Docker-only execution - No local commands
# Supports: CAC40, NASDAQ100, FTSE100, DAX40

# ========================================
# Variables
# ========================================

# Colors for terminal output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
BOLD := \033[1m
NC := \033[0m # No Color

# Docker configuration
DOCKER_COMPOSE_DEV := docker/docker-compose.dev.yml
DOCKER_COMPOSE_PROD := docker/docker-compose.prod.yml

# ========================================
# Main Commands (Docker-only execution)
# ========================================

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message (Docker-only execution)
	@echo "$(BOLD)Boursa Vision - Production API with Real YFinance Data$(NC)"
	@echo "$(BLUE)===============================================$(NC)"
	@echo "$(YELLOW)📈 Same FastAPI code works with Docker AND locally$(NC)"
	@echo "$(YELLOW)🚀 Production API with real financial data$(NC)"
	@echo "$(YELLOW)💼 Supports: CAC40, NASDAQ100, FTSE100, DAX40$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BOLD)Quick Start:$(NC)"
	@echo "$(GREEN)  make api             $(NC)# Start API with Docker (simple)"
	@echo "$(GREEN)  make api-local       $(NC)# Start API locally (same code)"
	@echo "$(GREEN)  make api-test        $(NC)# Test API endpoints"

# ========================================
# Production API Commands (Docker)
# ========================================

.PHONY: api
api: ## Start Production API with real YFinance data (simple Docker)
	@echo "$(YELLOW)🚀 Starting Production API with real financial data (direct Docker)...$(NC)"
	@echo "$(BLUE)🔧 Building Docker image...$(NC)"
	@cd backend && docker build -f ../docker/Dockerfile.backend --target development -t boursa-api .
	@echo "$(BLUE)🚀 Starting container...$(NC)"
	@docker run -d --name boursa-api-container \
		-p 8000:8000 \
		-e DOCKER_ENV=true \
		-e API_PORT=8000 \
		-e ENABLED_MARKET_INDICES=cac40,nasdaq100,ftse100,dax40 \
		boursa-api \
		sh -c "poetry run python main.py"
	@echo "$(GREEN)✅ Production API started successfully!$(NC)"
	@echo "$(BLUE)📊 API Endpoint: http://localhost:8000$(NC)"
	@echo "$(BLUE)💚 Health Check: http://localhost:8000/health$(NC)"
	@echo "$(BLUE)📚 Documentation: http://localhost:8000/docs$(NC)"
	@echo "$(BLUE)📋 API Info: http://localhost:8000/$(NC)"
	@echo "$(YELLOW)💼 Supported Indices: CAC40, NASDAQ100, FTSE100, DAX40$(NC)"

.PHONY: api-stop
api-stop: ## Stop Production API
	@echo "$(YELLOW)⏹️  Stopping Production API...$(NC)"
	@docker stop boursa-api-container 2>/dev/null || true
	@docker rm boursa-api-container 2>/dev/null || true
	@echo "$(GREEN)✅ Production API stopped$(NC)"

.PHONY: api-restart
api-restart: ## Restart Production API
	@$(MAKE) api-stop
	@$(MAKE) api
	@echo "$(GREEN)🔄 Production API restarted$(NC)"

.PHONY: api-logs
api-logs: ## Show Production API logs
	@echo "$(YELLOW)📋 Showing Production API logs...$(NC)"
	@cd docker && docker-compose -f docker-compose.dev.yml logs -f backend

.PHONY: api-build
api-build: ## Build Production API Docker image
	@echo "$(YELLOW)🔨 Building Production API Docker image...$(NC)"
	@cd docker && docker-compose -f docker-compose.dev.yml build backend
	@echo "$(GREEN)✅ Production API image built$(NC)"

.PHONY: api-rebuild
api-rebuild: ## Rebuild and restart Production API
	@echo "$(YELLOW)🔨 Rebuilding Production API...$(NC)"
	@$(MAKE) api-stop
	@$(MAKE) api-build
	@$(MAKE) api
	@echo "$(GREEN)🔄 Production API rebuilt and restarted$(NC)"

.PHONY: api-test
api-test: ## Test Production API endpoints with real data
	@echo "$(YELLOW)🧪 Testing Production API with real YFinance data...$(NC)"
	@echo "$(BLUE)Testing health endpoint...$(NC)"
	@curl -s http://localhost:8000/health | python3 -c "import json,sys; data=json.load(sys.stdin); print('🟢 Health Status:', data.get('status')); [print(f'  📈 {k}: {v.get(\"price\", \"N/A\")} {v.get(\"currency\", \"\")}') for k,v in data.get('real_data_tests', {}).items()]" 2>/dev/null || echo "$(RED)❌ API not responding. Run 'make api' first.$(NC)"
	@echo "$(GREEN)✅ API test completed$(NC)"

.PHONY: api-local
api-local: ## Start Production API locally (same code as Docker)
	@echo "$(YELLOW)🚀 Starting Production API locally with same code...$(NC)"
	@echo "$(BLUE)📊 API will start on: http://localhost:8001$(NC)"
	@echo "$(BLUE)📚 Documentation: http://localhost:8001/docs$(NC)"
	@echo "$(YELLOW)🔄 Hot-reload enabled$(NC)"
	@cd backend && API_PORT=8001 poetry run python main.py

.PHONY: api-shell
api-shell: ## Access Production API container shell
	@echo "$(YELLOW)🐳 Accessing Production API container shell...$(NC)"
	@cd docker && docker-compose -f docker-compose.dev.yml exec backend /bin/bash

# ========================================
# Database Commands (Docker)
# ========================================

.PHONY: db-logs
db-logs: ## Show database logs
	@echo "$(YELLOW)📋 Showing database logs...$(NC)"
	@cd docker && docker-compose -f docker-compose.dev.yml logs -f postgres

.PHONY: db-shell
db-shell: ## Access database shell
	@echo "$(YELLOW)🐳 Accessing database shell...$(NC)"
	@cd docker && docker-compose -f docker-compose.dev.yml exec postgres psql -U boursa_user -d boursa_vision

# ========================================
# System Commands
# ========================================

.PHONY: status
status: ## Show system status
	@echo "$(BOLD)📊 Boursa Vision - System Status$(NC)"
	@echo "=================================="
	@echo "$(YELLOW)🐳 Docker Containers:$(NC)"
	@cd docker && docker-compose -f docker-compose.dev.yml ps 2>/dev/null || echo "$(RED)❌ No containers running$(NC)"
	@echo ""
	@echo "$(YELLOW)🌐 Network Ports:$(NC)"
	@netstat -tulpn 2>/dev/null | grep -E ":(8000|5432|6379)" | head -5 || echo "$(YELLOW)⚠️  No services detected$(NC)"

.PHONY: clean
clean: ## Clean Docker containers and images
	@echo "$(YELLOW)🧹 Cleaning Docker resources...$(NC)"
	@cd docker && docker-compose -f docker-compose.dev.yml down --volumes --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)✅ Docker cleanup completed$(NC)"

.PHONY: logs
logs: ## Show all service logs
	@echo "$(YELLOW)📋 Showing all service logs...$(NC)"
	@cd docker && docker-compose -f docker-compose.dev.yml logs -f

# ========================================
# Development Shortcuts
# ========================================

.PHONY: start
start: api ## Shortcut: Start Production API

.PHONY: stop
stop: api-stop ## Shortcut: Stop Production API

.PHONY: restart
restart: api-restart ## Shortcut: Restart Production API

.PHONY: test
test: api-test ## Shortcut: Test Production API

.PHONY: build
build: api-build ## Shortcut: Build Production API
