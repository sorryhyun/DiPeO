# DiPeO Makefile

.PHONY: install codegen dev-server dev-web clean help lint format

# Default target
help:
	@echo "DiPeO Commands:"
	@echo "  make install   - Install all dependencies"
	@echo "  make codegen   - Generate code from domain models"
	@echo "  make dev-server - Run backend server"
	@echo "  make dev-web   - Run frontend server"
	@echo "  make lint      - Run all linters"
	@echo "  make format    - Format all code"
	@echo "  make clean     - Clean generated files"

# Combined install
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt -e ./apps/server -e ./apps/cli
	pnpm install
	@echo "✅ All dependencies installed!"

# Code generation
codegen:
	@echo "🔄 Generating code..."
	cd packages/domain-models && pnpm build
	pnpm --filter web codegen
	cd apps/cli && python scripts/generate_graphql_operations.py

# Development servers
dev-server:
	cd apps/server && python main.py

dev-web:
	pnpm -F web dev

# Python directories
PY_DIRS := apps/server apps/cli packages/python/dipeo_*

# Linting
lint:
	@echo "🔍 Linting..."
	@for dir in $(PY_DIRS); do \
		[ -d "$$dir/src" ] && (cd $$dir && ruff check src $$([ -d tests ] && echo tests)) || true; \
	done
	@cd apps/server && mypy src || true
	@cd apps/cli && mypy src || true
	pnpm run lint

# Formatting
format:
	@echo "✨ Formatting..."
	@for dir in $(PY_DIRS); do \
		[ -d "$$dir/src" ] && (cd $$dir && ruff format src $$([ -d tests ] && echo tests)) || true; \
	done

# Clean
clean:
	@echo "🧹 Cleaning..."
	find . -type d \( -name "__pycache__" -o -name "*.egg-info" -o -name ".pytest_cache" \
		-o -name ".ruff_cache" -o -name "__generated__" -o -name "dist" -o -name "build" \) \
		-exec rm -rf {} + 2>/dev/null || true
	rm -rf .logs/*.log 2>/dev/null || true
