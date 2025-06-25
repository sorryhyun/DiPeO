# DiPeO Makefile

.PHONY: install-py install-web install-cli install-all codegen build-all dev-server dev-web dev-all clean help lint-py format-py typecheck-py lint-all

# Default target
help:
	@echo "DiPeO Development Commands:"
	@echo "  make install-all    - Install all dependencies"
	@echo "  make install-py     - Install Python dependencies"
	@echo "  make install-web    - Install web dependencies"
	@echo "  make install-cli    - Install CLI in editable mode"
	@echo "  make codegen        - Generate code from domain models"
	@echo "  make build-all      - Build all components with proper order"
	@echo "  make dev-server     - Run development server"
	@echo "  make dev-web        - Run web development server"
	@echo "  make dev-all        - Instructions for running both servers"
	@echo "  make lint-py        - Run Python linter (ruff)"
	@echo "  make format-py      - Format Python code"
	@echo "  make typecheck-py   - Run Python type checker (mypy)"
	@echo "  make lint-all       - Run all linters"
	@echo "  make clean          - Clean generated files and caches"

# Install commands
install-py:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt
	pip install -e ./packages/python/dipeo_core
	pip install -e ./packages/python/dipeo_domain
	pip install -e ./apps/server

install-web:
	@echo "📦 Installing web dependencies..."
	pnpm install

install-cli:
	@echo "📦 Installing CLI..."
	pip install -e ./apps/cli

install-all: install-py install-web install-cli
	@echo "✅ All dependencies installed!"

# Code generation
codegen:
	@echo "🔄 Generating code from domain models..."
	cd packages/domain-models && pnpm build

# Build everything with proper dependency order
build-all:
	@echo "🔨 Building all components..."
	./build-all.sh

# Development servers
dev-server:
	@echo "🚀 Starting development server..."
	cd apps/server && python main.py

dev-web:
	@echo "🚀 Starting web development server..."
	pnpm -F web dev

dev-all:
	@echo "🚀 Starting all development servers..."
	@echo "Start backend in one terminal: make dev-server"
	@echo "Start frontend in another terminal: make dev-web"
	@echo "Or use tmux/screen to run both in parallel"

# Linting and formatting
lint-py:
	@echo "🔍 Running Python linter (ruff)..."
	cd apps/server && ruff check src tests
	cd apps/cli && ruff check src tests

format-py:
	@echo "✨ Formatting Python code..."
	cd apps/server && ruff format src tests
	cd apps/cli && ruff format src tests

typecheck-py:
	@echo "🔍 Running Python type checker (mypy)..."
	cd apps/server && mypy src
	cd apps/cli && mypy src

lint-all: lint-py typecheck-py
	@echo "🔍 Running TypeScript/JavaScript linter..."
	pnpm run lint
	@echo "✅ All linting complete!"

# Clean command
clean:
	@echo "🧹 Cleaning generated files and caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "__generated__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .logs/*.log 2>/dev/null || true
	@echo "✅ Clean complete!"
# Install pre-commit hooks
install-hooks:
	@echo "🔗 Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Pre-commit hooks installed!"
