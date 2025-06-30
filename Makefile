# DiPeO Makefile

.PHONY: install codegen dev-server dev-web dev-all clean help lint format graphql-schema

# Default target
help:
	@echo "DiPeO Commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make codegen      - Generate code from domain models (Python, GraphQL, CLI)"
	@echo "  make dev-all      - Run both backend and frontend servers"
	@echo "  make dev-server   - Run backend server"
	@echo "  make dev-web      - Run frontend server"
	@echo "  make graphql-schema - Export GraphQL schema from server"
	@echo "  make lint-{server, web, cli} - Run linters"
	@echo "  make format       - Format all code"
	@echo "  make clean        - Clean generated files"

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
	make graphql-schema
	pnpm --filter web codegen
	cd apps/cli && python scripts/generate_graphql_operations.py
	@echo "✅ All code generation completed!"

# Development servers
dev-server:
	cd apps/server && python main.py

dev-web:
	pnpm -F web dev

# Run both servers in parallel
dev-all:
	@echo "🚀 Starting all development servers..."
	@trap 'kill 0' INT; \
	(make dev-server 2>&1 | sed 's/^/[server] /' &) && \
	(sleep 3 && make dev-web 2>&1 | sed 's/^/[web] /' &) && \
	wait

# Export GraphQL schema
graphql-schema:
	@echo "📝 Exporting GraphQL schema..."
	cd apps/server && python -m dipeo_server.api.graphql.schema > schema.graphql
	@echo "✅ GraphQL schema exported to apps/server/schema.graphql"

# Python directories
PY_DIRS := apps/server apps/cli packages/python/dipeo_*

# Linting
lint-web:
	@echo "🔍 Linting..."
	pnpm run lint

lint-server:
	@echo "🔍 Linting..."
	@for dir in $(PY_DIRS); do \
		[ -d "$$dir/src" ] && (cd $$dir && ruff check --exclude="*/__generated__.py" src $$([ -d tests ] && echo tests)) || true; \
	done
	@cd apps/server && mypy src || true

lint-cli:
	@echo "🔍 Linting..."
	@for dir in $(PY_DIRS); do \
		[ -d "$$dir/src" ] && (cd $$dir && ruff check --exclude="*/__generated__.py" src $$([ -d tests ] && echo tests)) || true; \
	done
	@cd apps/cli && mypy src || true

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
