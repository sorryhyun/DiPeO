# DiPeO Makefile

.PHONY: install codegen codegen-node codegen-watch dev-server dev-web dev-all clean help lint format graphql-schema lint-imports

# Default target
help:
	@echo "DiPeO Commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make codegen      - Generate code from domain models (Python, GraphQL)"
	@echo "  make codegen-node NODE_SPEC=path/to/spec.json - Generate code for a specific node"
	@echo "  make codegen-watch - Watch node specifications for changes"
	@echo "  make dev-all      - Run both backend and frontend servers"
	@echo "  make dev-server   - Run backend server"
	@echo "  make dev-web      - Run frontend server"
	@echo "  make graphql-schema - Export GraphQL schema from server"
	@echo "  make lint-{server, web, cli} - Run linters"
	@echo "  make lint-imports - Check import dependencies"
	@echo "  make format       - Format all code"
	@echo "  make clean        - Clean generated files"

# Combined install
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	pip install -e ./apps/server -e ./apps/cli
	pnpm install
	@echo "✅ All dependencies installed!"

# Code generation
codegen:
	@echo "🔄 Generating code from domain models..."
	cd dipeo/models && pnpm generate:all
	@echo "🔄 Generating TypeScript types for frontend..."
	pnpm --filter web codegen
	@echo "✅ All code generation completed!"

# Generate code for a specific node type
codegen-node:
	@if [ -z "$(NODE_SPEC)" ]; then \
		echo "❌ Error: NODE_SPEC is required"; \
		echo "Usage: make codegen-node NODE_SPEC=path/to/spec.json"; \
		exit 1; \
	fi
	@echo "🔄 Generating code for node specification: $(NODE_SPEC)"
	@python scripts/run_codegen.py $(NODE_SPEC)
	@echo "✅ Node code generation completed!"

# Watch for changes in node specifications
codegen-watch:
	@echo "👀 Starting file watcher for node specifications..."
	@echo "Press Ctrl+C to stop watching"
	@python scripts/watch_codegen.py

# Development servers
dev-server:
	cd apps/server && DIPEO_BASE_DIR="$(shell pwd)" python main.py

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
	cd apps/server && PYTHONPATH="$(shell pwd):$$PYTHONPATH" DIPEO_BASE_DIR="$(shell pwd)" python -m dipeo_server.api.graphql.schema > schema.graphql
	@echo "✅ GraphQL schema exported to apps/server/schema.graphql"

# Python directories
PY_DIRS := apps/server apps/cli dipeo

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

# Import linting
lint-imports:
	@echo "🔍 Checking import dependencies..."
	@lint-imports || (echo "❌ Import violations found!" && exit 1)

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
