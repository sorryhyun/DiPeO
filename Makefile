# DiPeO Makefile

.PHONY: install codegen codegen-node codegen-watch dev-server dev-web dev-all clean help lint format graphql-schema diff-staged validate-staged validate-staged-syntax apply apply-syntax-only backup-generated

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
	@echo "  make format       - Format all code"
	@echo "  make clean        - Clean generated files"
	@echo ""
	@echo "Staging Commands:"
	@echo "  make diff-staged  - Show differences between staged and active generated files"
	@echo "  make validate-staged - Validate staged files with mypy type checking"
	@echo "  make validate-staged-syntax - Validate staged files (syntax only)"
	@echo "  make apply        - Apply staged changes with full validation"
	@echo "  make apply-syntax-only - Apply staged changes with syntax validation only"
	@echo "  make backup-generated - Backup current generated files before applying"

# Combined install
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	pip install -e ./apps/server -e ./apps/cli
	pnpm install
	@echo "All dependencies installed!"

# Diagram-based code generation (NEW DEFAULT)
codegen:
	@echo "Running unified diagram-based code generation..."
	dipeo run codegen/diagrams/models/generate_all_models --light --debug --timeout=15
	@sleep 1
	make apply-syntax-only
	dipeo run codegen/diagrams/backend/generate_backend --light --debug --timeout=10
	dipeo run codegen/diagrams/frontend/generate_frontend --light --debug --timeout=10
	make graphql-schema
	@echo "All code generation completed using DiPeO diagrams!"

# Diagram-based code generation for node UI
codegen-models:
	@echo "Running diagram-based model generation for all nodes..."
	dipeo run codegen/diagrams/models/generate_all_models --light --debug --timeout=30
	@echo "Diagram-based code generation completed!"

# Generate all nodes using diagram approach
codegen-backend:
	@echo "Generating UI for all node types using diagram..."
	dipeo run codegen/diagrams/backend/generate_backend --light --debug --timeout=30
	@echo "All nodes generated via diagram!"

codegen-frontend:
	@echo "Generating UI for all node types using diagram..."
	dipeo run codegen/diagrams/frontend/generate_frontend --light --debug --timeout=30
	@echo "All nodes generated via diagram!"


# Register generated nodes separately
register-nodes:
	@echo "Registering generated nodes..."
	@python files/codegen/code/node_registrar.py
	@echo "Node registration completed!"

# Watch for changes in node specifications
codegen-watch:
	@echo "Starting file watcher for node specifications..."
	@echo "Press Ctrl+C to stop watching"
	@python scripts/watch_codegen.py

# Development servers
dev-server:
	cd apps/server && DIPEO_BASE_DIR="$(shell pwd)" python main.py

dev-web:
	pnpm -F web dev

# Run both servers in parallel
dev-all:
	@echo "Starting all development servers..."
	@trap 'kill 0' INT; \
	(make dev-server 2>&1 | sed 's/^/[server] /' &) && \
	(sleep 3 && make dev-web 2>&1 | sed 's/^/[web] /' &) && \
	wait

# Export GraphQL schema
graphql-schema:
	@echo "Exporting GraphQL schema from application layer..."
	PYTHONPATH="$(shell pwd):$$PYTHONPATH" DIPEO_BASE_DIR="$(shell pwd)" python -m dipeo.application.graphql.export_schema apps/server/schema.graphql
	@echo "GraphQL schema exported to apps/server/schema.graphql"
	@echo "Generating GraphQL TypeScript types..."
	pnpm --filter web codegen
	@echo "GraphQL TypeScript types generated!"

# Python directories
PY_DIRS := apps/server apps/cli dipeo

# Linting
lint-web:
	@echo "Linting..."
	pnpm run lint

lint-server:
	@echo "Linting..."
	@for dir in $(PY_DIRS); do \
		[ -d "$$dir/src" ] && (cd $$dir && ruff check --exclude="*/__generated__.py" src $$([ -d tests ] && echo tests)) || true; \
	done
	@cd apps/server && mypy src || true

lint-cli:
	@echo "Linting..."
	@for dir in $(PY_DIRS); do \
		[ -d "$$dir/src" ] && (cd $$dir && ruff check --exclude="*/__generated__.py" src $$([ -d tests ] && echo tests)) || true; \
	done
	@cd apps/cli && mypy src || true

# Formatting
format:
	@echo "Formatting..."
	@for dir in $(PY_DIRS); do \
		[ -d "$$dir/src" ] && (cd $$dir && ruff format src $$([ -d tests ] && echo tests)) || true; \
	done

# Staging Commands
diff-staged:
	@echo "Showing differences between staged and active generated files..."
	@diff -rq dipeo/diagram_generated dipeo/diagram_generated_staged 2>/dev/null || true
	@echo ""
	@echo "For detailed diffs, run: diff -r dipeo/diagram_generated dipeo/diagram_generated_staged"

validate-staged:
	@echo "Validating staged Python files..."
	@if [ ! -d "dipeo/diagram_generated_staged" ]; then \
		echo "Error: No staged directory found. Run 'make codegen-models' first."; \
		exit 1; \
	fi
	@echo "Running Python compilation check..."
	@find dipeo/diagram_generated_staged -name "*.py" -type f | xargs python -m py_compile || \
		(echo "Python compilation check failed!" && exit 1)
	@echo "Running mypy type check on staged files only..."
	@PYTHONPATH="$(shell pwd):$$PYTHONPATH" mypy dipeo/diagram_generated_staged \
		--ignore-missing-imports \
		--no-error-summary \
		--exclude "__pycache__" \
		--follow-imports=skip \
		--no-implicit-reexport || \
		(echo "Mypy type check failed!" && exit 1)
	@echo "All validation checks passed!"

validate-staged-syntax:
	@echo "Validating staged Python files (syntax only)..."
	@if [ ! -d "dipeo/diagram_generated_staged" ]; then \
		echo "Error: No staged directory found. Run 'make codegen-models' first."; \
		exit 1; \
	fi
	@echo "Running Python compilation check..."
	@find dipeo/diagram_generated_staged -name "*.py" -type f | xargs python -m py_compile || \
		(echo "Python compilation check failed!" && exit 1)
	@echo "Python syntax validation passed!"

apply: validate-staged
	@echo "Applying staged changes to active directory..."
	@if [ ! -d "dipeo/diagram_generated_staged" ]; then \
		echo "Error: No staged directory found. Run 'make codegen' first."; \
		exit 1; \
	fi
	@echo "Copying staged files to active directory..."
	@cp -r dipeo/diagram_generated_staged/* dipeo/diagram_generated/
	@echo "Staged changes applied successfully!"

apply-syntax-only: validate-staged-syntax
	@echo "Applying staged changes to active directory (syntax validation only)..."
	@if [ ! -d "dipeo/diagram_generated_staged" ]; then \
		echo "Error: No staged directory found. Run 'make codegen' first."; \
		exit 1; \
	fi
	@echo "Copying staged files to active directory..."
	@cp -r dipeo/diagram_generated_staged/* dipeo/diagram_generated/
	@echo "Staged changes applied successfully!"

backup-generated:
	@echo "Backing up current generated files..."
	@mkdir -p .backups
	@tar -czf .backups/diagram_generated.backup.$$(date +%Y%m%d_%H%M%S).tar.gz dipeo/diagram_generated/
	@echo "Backup created in .backups/"

# Clean
clean:
	@echo "Cleaning..."
	find . -type d \( -name "__pycache__" -o -name "*.egg-info" -o -name ".pytest_cache" \
		-o -name ".ruff_cache" -o -name "__generated__" -o -name "dist" -o -name "build" \) \
		-exec rm -rf {} + 2>/dev/null || true
	rm -rf .logs/*.log 2>/dev/null || true
