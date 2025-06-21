# DiPeO Makefile

.PHONY: install-py install-web install-cli install-all codegen dev-server dev-web dev-all clean help

# Default target
help:
	@echo "DiPeO Development Commands:"
	@echo "  make install-all    - Install all dependencies"
	@echo "  make install-py     - Install Python dependencies"
	@echo "  make install-web    - Install web dependencies"
	@echo "  make install-cli    - Install CLI in editable mode"
	@echo "  make codegen        - Generate code from domain models"
	@echo "  make dev-server     - Run development server"
	@echo "  make dev-web        - Run web development server"
	@echo "  make dev-all        - Run both servers"
	@echo "  make clean          - Clean generated files and caches"

# Install commands
install-py:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt
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
	./codegen.sh

# Development servers
dev-server:
	@echo "🚀 Starting development server..."
	cd apps/server && python main.py

dev-web:
	@echo "🚀 Starting web development server..."
	pnpm -F @dipeo/web dev

dev-all:
	@echo "🚀 Starting all development servers..."
	./dev.sh --all

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