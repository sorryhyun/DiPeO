# DiPeO Makefile

.PHONY: install codegen codegen-node codegen-watch dev-server dev-web dev-all clean help lint format graphql-schema lint-imports diff-staged apply backup-generated

# Default target
help:
	@echo "DiPeO Commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make codegen      - Generate all code using diagram-based approach"
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
	@echo ""
	@echo "Staging Commands:"
	@echo "  make diff-staged  - Show differences between staged and active generated files"
	@echo "  make apply        - Apply staged changes to active directory"
	@echo "  make backup-generated - Backup current generated files before applying"

# Combined install
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	pip install -e ./apps/server -e ./apps/cli
	pnpm install
	@echo "✅ All dependencies installed!"

# Diagram-based code generation (NEW DEFAULT)
codegen:
	@echo "🚀 Running unified diagram-based code generation..."
	dipeo run codegen/diagrams/generate_all --light --debug --no-browser --timeout=120
	@echo "✅ All code generation completed using DiPeO diagrams!"

# Diagram-based code generation for node UI
codegen-models:
	@echo "🎨 Running diagram-based model generation for all nodes..."
	dipeo run codegen/diagrams/models/generate_all_models --light --debug --no-browser --timeout=30
	@echo "✅ Diagram-based code generation completed!"

# Generate all nodes using diagram approach
codegen-backend:
	@echo "🎨 Generating UI for all node types using diagram..."
	dipeo run codegen/diagrams/backend/generate_backend --light --debug --no-browser --timeout=30
	@echo "✅ All nodes generated via diagram!"

codegen-frontend:
	@echo "🎨 Generating UI for all node types using diagram..."
	dipeo run codegen/diagrams/frontend/generate_frontend --light --debug --no-browser --timeout=30
	@echo "✅ All nodes generated via diagram!"


# Register generated nodes separately
register-nodes:
	@echo "📝 Registering generated nodes..."
	@python files/codegen/code/node_registrar.py
	@echo "✅ Node registration completed!"

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
	@echo "🔄 Generating GraphQL TypeScript types..."
	pnpm --filter web codegen
	@echo "✅ GraphQL TypeScript types generated!"

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

# Staging Commands
diff-staged:
	@echo "📊 Showing differences between staged and active generated files..."
	@diff -rq dipeo/diagram_generated dipeo/diagram_generated_staged 2>/dev/null || true
	@echo ""
	@echo "For detailed diffs, run: diff -r dipeo/diagram_generated dipeo/diagram_generated_staged"

apply:
	@echo "📋 Applying staged changes to active directory..."
	@if [ ! -d "dipeo/diagram_generated_staged" ]; then \
		echo "❌ Error: No staged directory found. Run 'make codegen' first."; \
		exit 1; \
	fi
	@echo "✅ Copying staged files to active directory..."
	@cp -r dipeo/diagram_generated_staged/* dipeo/diagram_generated/
	@echo "✅ Staged changes applied successfully!"

backup-generated:
	@echo "💾 Backing up current generated files..."
	@mkdir -p .backups
	@tar -czf .backups/diagram_generated.backup.$$(date +%Y%m%d_%H%M%S).tar.gz dipeo/diagram_generated/
	@echo "✅ Backup created in .backups/"

# Clean
clean:
	@echo "🧹 Cleaning..."
	find . -type d \( -name "__pycache__" -o -name "*.egg-info" -o -name ".pytest_cache" \
		-o -name ".ruff_cache" -o -name "__generated__" -o -name "dist" -o -name "build" \) \
		-exec rm -rf {} + 2>/dev/null || true
	rm -rf .logs/*.log 2>/dev/null || true
