# DiPeO Makefile

.PHONY: install install-dev codegen codegen-auto codegen-watch codegen-status dev-server dev-web dev-all clean clean-staged help lint-server lint-web lint-cli format graphql-schema diff-staged validate-staged validate-staged-syntax apply apply-syntax-only backup-generated

# Default target
help:
	@echo "DiPeO Commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make install-dev  - Install development dependencies (linters, formatters, etc.)"
	@echo ""
	@echo "Code Generation (Recommended Workflow):"
	@echo "  make codegen      - Generate all code to staging directory (safe)"
	@echo "  make diff-staged  - Review changes before applying"
	@echo "  make apply-syntax-only - Apply staged changes with syntax validation"
	@echo "  make graphql-schema - Update GraphQL schema and TypeScript types"
	@echo ""
	@echo "Code Generation (Quick Commands):"
	@echo "  make codegen-auto - ⚠️ DANGEROUS: Generate + auto-apply + schema update"
	@echo "  make codegen-watch - Watch node specifications for changes"
	@echo "  make codegen-status - Check current code generation state"
	@echo ""
	@echo "Development:"
	@echo "  make dev-all      - Run both backend and frontend servers"
	@echo "  make dev-server   - Run backend server"
	@echo "  make dev-web      - Run frontend server"
	@echo ""
	@echo "Quality & Testing:"
	@echo "  make lint-{server, web, cli} - Run linters"
	@echo "  make format       - Format all code"
	@echo ""
	@echo "Staging Management:"
	@echo "  make validate-staged - Validate staged files with mypy type checking"
	@echo "  make validate-staged-syntax - Validate staged files (syntax only)"
	@echo "  make apply        - Apply staged changes with full validation"
	@echo "  make backup-generated - Backup current generated files before applying"
	@echo "  make clean-staged - Clean staged files only"
	@echo "  make clean        - Clean all generated files and caches"

# Combined install
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	pnpm install
	@echo "All dependencies installed!"

# Install development dependencies
install-dev: install
	@echo "Installing development dependencies..."
	pip install import-linter black mypy "ruff>=0.8.0" pytest-asyncio pytest-cov isort
	@echo "Development dependencies installed!"

# Primary code generation command (SAFE - stages changes for review)
codegen:
	@echo "======================================"
	@echo "Starting unified code generation..."
	@echo "======================================"
	@echo ""
	@echo "This will generate all code to the staging directory."
	@echo "You can review changes before applying them."
	@echo ""
	dipeo run codegen/diagrams/generate_all --light --debug --timeout=90
	@echo ""
	@echo "======================================"
	@echo "Code generation complete!"
	@echo "======================================"
	@echo ""
	@echo "Generated files are in: dipeo/diagram_generated_staged/"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Review changes:    make diff-staged"
	@echo "  2. Apply changes:     make apply-syntax-only"
	@echo "  3. Update GraphQL:    make graphql-schema"
	@echo ""

# Automatic code generation with auto-apply (DANGEROUS - use with caution!)
codegen-auto:
	@echo "⚠️  WARNING: This command automatically applies all changes!"
	@echo "Running unified code generation with auto-apply..."
	@echo ""
	dipeo run codegen/diagrams/generate_all --light --debug --timeout=90
	@sleep 1
	@echo "Applying staged changes to active directory (syntax validation only)..."
	@if [ ! -d "dipeo/diagram_generated_staged" ]; then \
		echo "Error: No staged directory found."; \
		exit 1; \
	fi
	@echo "Copying staged files to active directory..."
	@cp -r dipeo/diagram_generated_staged/* dipeo/diagram_generated/
	@echo "Staged changes applied successfully!"
	@echo "Exporting GraphQL schema..."
	PYTHONPATH="$(shell pwd):$$PYTHONPATH" DIPEO_BASE_DIR="$(shell pwd)" python -m dipeo.application.graphql.export_schema apps/server/schema.graphql
	@echo "Generating TypeScript types..."
	pnpm --filter web codegen
	@echo ""
	@echo "✓ All code generation and application completed!"

# Watch for changes in node specifications
codegen-watch:
	@echo "Starting file watcher for node specifications..."
	@echo "Press Ctrl+C to stop watching"
	@python scripts/watch_codegen.py

# Check code generation status
codegen-status:
	@echo "======================================"
	@echo "Code Generation Status"
	@echo "======================================"
	@echo ""
	@if [ -d "dipeo/diagram_generated_staged" ]; then \
		echo "✓ Staged directory exists"; \
		echo "  Files: $$(find dipeo/diagram_generated_staged -type f | wc -l)"; \
		echo "  Last modified: $$(stat -c %y dipeo/diagram_generated_staged 2>/dev/null || stat -f %Sm dipeo/diagram_generated_staged 2>/dev/null)"; \
	else \
		echo "✗ No staged directory found"; \
	fi
	@echo ""
	@if [ -d "dipeo/diagram_generated" ]; then \
		echo "✓ Active generated directory exists"; \
		echo "  Files: $$(find dipeo/diagram_generated -type f | wc -l)"; \
		echo "  Last modified: $$(stat -c %y dipeo/diagram_generated 2>/dev/null || stat -f %Sm dipeo/diagram_generated 2>/dev/null)"; \
	else \
		echo "✗ No active generated directory found"; \
	fi
	@echo ""
	@if [ -d "temp/codegen" ] || [ -d "temp/core" ] || [ -d "temp/specifications" ]; then \
		echo "✓ Cached AST files exist"; \
	else \
		echo "✗ No cached AST files found"; \
	fi
	@echo ""

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
	@echo "======================================"
	@echo "Comparing staged vs active generated files..."
	@echo "======================================"
	@if [ ! -d "dipeo/diagram_generated_staged" ]; then \
		echo "No staged directory found. Run 'make codegen' first."; \
		exit 1; \
	fi
	@diff -rq dipeo/diagram_generated dipeo/diagram_generated_staged 2>/dev/null || true
	@echo ""
	@echo "For detailed diffs, run:"
	@echo "  diff -r dipeo/diagram_generated dipeo/diagram_generated_staged | less"
	@echo ""
	@echo "To apply staged changes, run:"
	@echo "  make apply-syntax-only  # Quick, syntax check only"
	@echo "  make apply              # Full validation with mypy"

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

# Clean staged files only
clean-staged:
	@echo "Cleaning staged generated files..."
	@rm -rf dipeo/diagram_generated_staged
	@echo "Staged files cleaned."

# Clean all generated files
clean:
	@echo "Cleaning all generated files and caches..."
	find . -type d \( -name "__pycache__" -o -name "*.egg-info" -o -name ".pytest_cache" \
		-o -name ".ruff_cache" -o -name "__generated__" -o -name "dist" -o -name "build" \) \
		-exec rm -rf {} + 2>/dev/null || true
	rm -rf .logs/*.log 2>/dev/null || true
	rm -rf temp/codegen temp/core temp/specifications 2>/dev/null || true
	@echo "Clean complete."
