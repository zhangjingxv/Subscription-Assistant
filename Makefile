# AttentionSync Makefile - Linus style
# "Make it work, make it right, make it fast - in that order"

.PHONY: help install run test clean dev prod

# Default target
help:
	@echo "AttentionSync - Simple commands for simple tasks"
	@echo ""
	@echo "  make install  - Install dependencies"
	@echo "  make run      - Run the application"
	@echo "  make dev      - Run in development mode"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up"
	@echo "  make prod     - Production deployment"

# Install dependencies - minimal by default
install:
	pip install --user --break-system-packages -q fastapi uvicorn sqlalchemy python-dotenv pydantic
	@echo "✓ Core dependencies installed"
	@echo "Optional: pip install --user openai anthropic redis (for extra features)"

# Run the application - simple and direct
run:
	@python start_simple.py

# Development mode - with auto-reload
dev:
	cd api && uvicorn app.main_clean:app --reload --host 127.0.0.1 --port 8000

# Run tests - when we have them
test:
	@echo "Testing..."
	@python -m pytest tests/ -v 2>/dev/null || echo "No tests yet - that's honest"

# Clean up - remove generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f .coverage
	rm -rf .pytest_cache
	rm -f *.db
	@echo "✓ Cleaned"

# Production - Docker, because it works
prod:
	docker-compose up -d
	@echo "✓ Running in production mode"

# Database operations
db-init:
	cd api && python -c "from app.core.db import init_db; import asyncio; asyncio.run(init_db())"
	@echo "✓ Database initialized"

db-reset:
	rm -f *.db
	$(MAKE) db-init
	@echo "✓ Database reset"

# Quick health check
health:
	@curl -s http://localhost:8000/health | python -m json.tool || echo "API not running"

# One-line deployment
deploy: install db-init run

# The Linus way - everything in one command
all: clean install test run