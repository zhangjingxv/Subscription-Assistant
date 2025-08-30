# AttentionSync Makefile
# Convenient commands for development and deployment

.PHONY: help
help: ## Show this help message
	@echo "AttentionSync - Make Commands"
	@echo ""
	@echo "Usage: make [command]"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================
# Environment Setup
# ============================================

.PHONY: init
init: ## Initialize the project (first time setup)
	@echo "🚀 Initializing AttentionSync..."
	@cp -n .env.example .env || true
	@echo "✅ Environment file created (please update .env with your values)"
	@make install
	@make db-init
	@echo "✨ Setup complete! Run 'make dev' to start development server"

.PHONY: install
install: ## Install all dependencies
	@echo "📦 Installing dependencies..."
	@cd api && pip install -r requirements.txt
	@cd web && npm install
	@cd worker && pip install -r requirements.txt
	@echo "✅ Dependencies installed"

.PHONY: update
update: ## Update all dependencies
	@echo "🔄 Updating dependencies..."
	@cd api && pip install -r requirements.txt --upgrade
	@cd web && npm update
	@cd worker && pip install -r requirements.txt --upgrade
	@echo "✅ Dependencies updated"

# ============================================
# Docker Commands
# ============================================

.PHONY: up
up: ## Start all services with docker-compose
	@echo "🐳 Starting services..."
	@docker-compose up -d
	@echo "✅ Services started"
	@echo "📱 Web UI: http://localhost:3000"
	@echo "🔌 API: http://localhost:8000"
	@echo "📊 MinIO: http://localhost:9001"

.PHONY: down
down: ## Stop all services
	@echo "🛑 Stopping services..."
	@docker-compose down
	@echo "✅ Services stopped"

.PHONY: restart
restart: ## Restart all services
	@make down
	@make up

.PHONY: logs
logs: ## Show logs from all services
	@docker-compose logs -f

.PHONY: logs-api
logs-api: ## Show API logs
	@docker-compose logs -f api

.PHONY: logs-worker
logs-worker: ## Show worker logs
	@docker-compose logs -f worker

.PHONY: logs-web
logs-web: ## Show web logs
	@docker-compose logs -f web

.PHONY: ps
ps: ## Show running services
	@docker-compose ps

.PHONY: build
build: ## Build all Docker images
	@echo "🔨 Building Docker images..."
	@docker-compose build
	@echo "✅ Images built"

.PHONY: rebuild
rebuild: ## Rebuild and restart all services
	@make down
	@make build
	@make up

# ============================================
# Development Commands
# ============================================

.PHONY: dev
dev: ## Start development environment
	@echo "💻 Starting development environment..."
	@docker-compose up -d postgres redis minio
	@cd api && uvicorn main:app --reload --port 8000 &
	@cd worker && celery -A app.celery worker --loglevel=info &
	@cd worker && celery -A app.celery beat --loglevel=info &
	@cd web && npm run dev
	@echo "✅ Development environment started"

.PHONY: dev-api
dev-api: ## Start API development server
	@cd api && uvicorn main:app --reload --port 8000

.PHONY: dev-web
dev-web: ## Start web development server
	@cd web && npm run dev

.PHONY: dev-worker
dev-worker: ## Start worker in development mode
	@cd worker && celery -A app.celery worker --loglevel=debug

# ============================================
# Database Commands
# ============================================

.PHONY: db-init
db-init: ## Initialize database schema
	@echo "🗄️ Initializing database..."
	@docker-compose up -d postgres
	@sleep 5
	@docker-compose exec -T postgres psql -U attentionsync -d attentionsync < infra/schemas.sql
	@echo "✅ Database initialized"

.PHONY: db-migrate
db-migrate: ## Run database migrations
	@echo "🔄 Running migrations..."
	@cd api && alembic upgrade head
	@echo "✅ Migrations complete"

.PHONY: db-reset
db-reset: ## Reset database (WARNING: destroys all data!)
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		make db-init; \
		echo "✅ Database reset complete"; \
	else \
		echo "❌ Operation cancelled"; \
	fi

.PHONY: db-backup
db-backup: ## Backup database
	@echo "💾 Backing up database..."
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U attentionsync attentionsync | gzip > backups/backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "✅ Backup complete"

.PHONY: db-restore
db-restore: ## Restore database from latest backup
	@echo "📥 Restoring database..."
	@gunzip -c $$(ls -t backups/*.sql.gz | head -1) | docker-compose exec -T postgres psql -U attentionsync attentionsync
	@echo "✅ Restore complete"

# ============================================
# Testing Commands
# ============================================

.PHONY: test
test: ## Run all tests
	@echo "🧪 Running tests..."
	@make test-api
	@make test-web
	@make test-worker
	@echo "✅ All tests passed"

.PHONY: test-api
test-api: ## Run API tests
	@cd api && pytest tests/ -v --cov=app --cov-report=term-missing

.PHONY: test-web
test-web: ## Run web tests
	@cd web && npm test

.PHONY: test-worker
test-worker: ## Run worker tests
	@cd worker && pytest tests/ -v

.PHONY: test-e2e
test-e2e: ## Run end-to-end tests
	@cd tests && npm run e2e

.PHONY: lint
lint: ## Run linters
	@echo "🔍 Running linters..."
	@cd api && black . --check && flake8 . && mypy .
	@cd web && npm run lint
	@cd worker && black . --check && flake8 .
	@echo "✅ Linting complete"

.PHONY: format
format: ## Format code
	@echo "✨ Formatting code..."
	@cd api && black . && isort .
	@cd web && npm run format
	@cd worker && black . && isort .
	@echo "✅ Formatting complete"

# ============================================
# Production Commands
# ============================================

.PHONY: prod
prod: ## Start production environment
	@echo "🚀 Starting production environment..."
	@docker-compose --profile production up -d
	@echo "✅ Production environment started"

.PHONY: prod-build
prod-build: ## Build for production
	@echo "📦 Building for production..."
	@cd web && npm run build
	@docker-compose --profile production build
	@echo "✅ Production build complete"

.PHONY: deploy
deploy: ## Deploy to production
	@echo "🚢 Deploying to production..."
	@make prod-build
	@make prod
	@echo "✅ Deployment complete"

# ============================================
# Monitoring Commands
# ============================================

.PHONY: monitor
monitor: ## Start monitoring stack (Prometheus + Grafana)
	@echo "📊 Starting monitoring..."
	@docker-compose --profile monitoring up -d
	@echo "✅ Monitoring started"
	@echo "📊 Prometheus: http://localhost:9090"
	@echo "📈 Grafana: http://localhost:3001 (admin/admin)"

.PHONY: metrics
metrics: ## Show current metrics
	@curl -s http://localhost:8000/metrics | head -20

# ============================================
# Utility Commands
# ============================================

.PHONY: shell-api
shell-api: ## Open shell in API container
	@docker-compose exec api bash

.PHONY: shell-worker
shell-worker: ## Open shell in worker container
	@docker-compose exec worker bash

.PHONY: shell-db
shell-db: ## Open PostgreSQL shell
	@docker-compose exec postgres psql -U attentionsync attentionsync

.PHONY: redis-cli
redis-cli: ## Open Redis CLI
	@docker-compose exec redis redis-cli

.PHONY: clean
clean: ## Clean up temporary files and caches
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

.PHONY: reset
reset: ## Reset everything (WARNING: destroys all data!)
	@echo "⚠️  WARNING: This will delete ALL data and containers!"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v --remove-orphans; \
		make clean; \
		echo "✅ Reset complete"; \
	else \
		echo "❌ Operation cancelled"; \
	fi

.PHONY: info
info: ## Show system information
	@echo "ℹ️  AttentionSync System Information"
	@echo "====================================="
	@echo "Docker version: $$(docker --version)"
	@echo "Docker Compose version: $$(docker-compose --version)"
	@echo "Python version: $$(python --version)"
	@echo "Node version: $$(node --version)"
	@echo "NPM version: $$(npm --version)"
	@echo ""
	@echo "Services status:"
	@docker-compose ps

.PHONY: check
check: ## Check system requirements
	@echo "🔍 Checking system requirements..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is not installed"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is not installed"; exit 1; }
	@command -v python >/dev/null 2>&1 || { echo "❌ Python is not installed"; exit 1; }
	@command -v node >/dev/null 2>&1 || { echo "❌ Node.js is not installed"; exit 1; }
	@command -v npm >/dev/null 2>&1 || { echo "❌ NPM is not installed"; exit 1; }
	@echo "✅ All requirements met"

# ============================================
# Release Commands
# ============================================

.PHONY: version
version: ## Show current version
	@cat VERSION

.PHONY: release
release: ## Create a new release
	@echo "📦 Creating release..."
	@read -p "Version (current: $$(cat VERSION)): " version; \
	echo $$version > VERSION; \
	git add .; \
	git commit -m "Release v$$version"; \
	git tag -a v$$version -m "Release v$$version"; \
	echo "✅ Release v$$version created"
	@echo "📤 Don't forget to push: git push origin main --tags"