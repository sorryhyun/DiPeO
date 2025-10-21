# Now using uv for Python dependency management
# Activate virtual environment with: source .venv/bin/activate

.PHONY: install install-dev install-uv sync-deps parse-typescript codegen codegen-auto codegen-watch codegen-status dev-server dev-web dev-widgets dev-all clean clean-staged help lint-server lint-web lint-cli format graphql-schema diff-staged validate-staged validate-staged-syntax apply apply-syntax-only backup-generated schema-docs docs-add-anchors-dry docs-add-anchors docs-validate-anchors docs-update build-widgets

# Default target
help:
	@echo "DiPeO Commands (using uv for Python dependencies):"
	@echo "  make install      - Install all dependencies (installs uv if needed)"
	@echo "  make install-dev  - Install development dependencies (linters, formatters, etc.)"
	@echo "  make install-uv   - Install uv package manager only"
	@echo "  make sync-deps    - Sync Python dependencies with uv"
	@echo ""
	@echo "Code Generation (Recommended Workflow):"
	@echo "  make parse-typescript - Parse TypeScript models to generate AST cache"
	@echo "  make codegen      - Generate all code to staging directory (includes parse-typescript)"
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
	@echo "  make dev-widgets  - Run widgets dev server"
	@echo "  make build-widgets - Build ChatGPT widgets"
	@echo ""
	@echo "Quality & Testing:"
	@echo "  make lint-{server, web, cli} - Run linters"
	@echo "  make format       - Format all code"
	@echo ""
	@echo "Documentation:"
	@echo "  make schema-docs           - Generate database schema documentation"
	@echo "  make docs-add-anchors-dry  - Preview adding anchors to documentation"
	@echo "  make docs-add-anchors      - Add anchors to features/formats/projects docs"
	@echo "  make docs-validate-anchors - Validate router skill anchor references"
	@echo "  make docs-update           - Full documentation update (anchors + validate)"
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
	@command -v uv >/dev/null 2>&1 || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	@export PATH="$$HOME/.local/bin:$$PATH" && uv sync
	@export PATH="$$HOME/.local/bin:$$PATH" && uv pip install -e dipeo -e apps/server
	pnpm install
	@echo "All dependencies installed!"
	@echo "Activate the virtual environment with: source .venv/bin/activate"

# Install uv if not present
install-uv:
	@command -v uv >/dev/null 2>&1 || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	@echo "uv is installed. Add to PATH with: export PATH=\"$$HOME/.local/bin:$$PATH\""

# Sync dependencies using uv
sync-deps:
	@export PATH="$$HOME/.local/bin:$$PATH" && uv sync --all-extras
	@echo "Dependencies synced with uv"

# Install development dependencies
install-dev: install
	@echo "Installing development dependencies..."
	@export PATH="$$HOME/.local/bin:$$PATH" && uv pip install import-linter black mypy "ruff>=0.8.0" pytest-asyncio pytest-cov isort
	@echo "Development dependencies installed!"

# Parse TypeScript models to generate AST cache
# Parse TypeScript specs to prepare for code generation
parse-typescript:
	@echo "Cleaning TypeScript AST cache..."
	@rm -rf temp/core temp/specifications temp/frontend temp/codegen temp/nodes temp/utilities temp/*.json 2>/dev/null || true
	@echo "Parsing TypeScript models..."
	@if command -v dipeo >/dev/null 2>&1; then \
		DIPEO_BASE_DIR=$(shell pwd) dipeo run projects/codegen/diagrams/parse_typescript_batch_direct --light --debug --simple --timeout=20; \
	else \
		DIPEO_BASE_DIR=$(shell pwd) uv run dipeo run projects/codegen/diagrams/parse_typescript_batch_direct --light --debug --timeout=20; \
	fi
	@echo "✓ TypeScript parsing complete"

# Primary code generation command (SAFE - stages changes for review)
# Generates Python code from TypeScript specs to staging directory
codegen: parse-typescript
	@echo "Starting code generation..."
	@if command -v dipeo >/dev/null 2>&1; then \
		DIPEO_BASE_DIR=$(shell pwd) dipeo run projects/codegen/diagrams/generate_all --light --debug --simple --timeout=35; \
	else \
		DIPEO_BASE_DIR=$(shell pwd) uv run dipeo run projects/codegen/diagrams/generate_all --light --debug --timeout=35; \
	fi
	@echo "✓ Code generation complete. Next: make apply-test→ make graphql-schema"

# Automatic code generation with auto-apply (DANGEROUS - use with caution!)
# Runs entire workflow: parse → generate → apply → update GraphQL
codegen-auto: parse-typescript
	@echo "⚠️  WARNING: Auto-applying all changes!"
	@if command -v dipeo >/dev/null 2>&1; then \
		DIPEO_BASE_DIR=$(shell pwd) dipeo run projects/codegen/diagrams/generate_all --light --simple --timeout=45; \
	else \
		DIPEO_BASE_DIR=$(shell pwd) uv run dipeo run projects/codegen/diagrams/generate_all --light --timeout=45; \
	fi
	@sleep 1
	@if [ ! -d "dipeo/diagram_generated_staged" ]; then \
		echo "Error: No staged directory found."; \
		exit 1; \
	fi
	@cp -r dipeo/diagram_generated_staged/* dipeo/diagram_generated/
	PYTHONPATH="$(shell pwd):$$PYTHONPATH" DIPEO_BASE_DIR="$(shell pwd)" python -m dipeo.application.graphql.export_schema apps/server/schema.graphql
	pnpm --filter web codegen
	@echo "✓ Code generation and application completed!"

# Watch for changes in node specifications
codegen-watch:
	@echo "Watch mode is no longer supported (watch_codegen.py has been removed)"

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
	DIPEO_BASE_DIR="$(shell pwd)" python apps/server/main.py

dev-web:
	pnpm -F web dev

dev-widgets:
	pnpm -F @dipeo/chatgpt-widgets dev

# Run both servers in parallel
dev-all:
	@echo "Starting all development servers..."
	@trap 'kill 0' INT; \
	(make dev-server 2>&1 | sed 's/^/[server] /' &) && \
	(sleep 3 && make dev-web 2>&1 | sed 's/^/[web] /' &) && \
	wait

# Build ChatGPT widgets
build-widgets:
	@echo "Generating GraphQL types for ChatGPT widgets..."
	pnpm --filter @dipeo/chatgpt-widgets codegen
	@echo "Building ChatGPT widgets..."
	pnpm -F @dipeo/chatgpt-widgets build
	@echo "Widgets built to apps/server/static/widgets/"

# Export GraphQL schema
graphql-schema:
	@echo "Exporting GraphQL schema from application layer..."
	PYTHONPATH="$(shell pwd):$$PYTHONPATH" DIPEO_BASE_DIR="$(shell pwd)" python -m dipeo.application.graphql.export_schema apps/server/schema.graphql
	@echo "GraphQL schema exported to apps/server/schema.graphql"
	@echo "Generating GraphQL TypeScript types for web..."
	pnpm --filter web codegen
	@echo "Generating GraphQL TypeScript types for chatgpt-widgets..."
	pnpm --filter @dipeo/chatgpt-widgets codegen
	@echo "GraphQL TypeScript types generated!"

# Python directories
PY_DIRS := apps/server dipeo

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
	@cd apps/server && mypy src || true

# Formatting
format:
	@echo "Formatting..."
	@for dir in $(PY_DIRS); do \
		[ -d "$$dir/src" ] && (cd $$dir && ruff format src $$([ -d tests ] && echo tests)) || true; \
	done

# Staging Commands
# Compare staged generated code with active generated code
diff-staged:
	@echo "======================================"
	@echo "Comparing staged vs active generated files..."
	@echo "======================================"
	@if [ ! -d "dipeo/diagram_generated_staged" ]; then \
		echo "No staged directory found. Run 'make codegen' first."; \
		exit 1; \
	fi
	@diff -rq -x '*.pyc' dipeo/diagram_generated dipeo/diagram_generated_staged 2>/dev/null || true
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
	@find dipeo/diagram_generated_staged -name "*.py" -type f | xargs uv run python -m py_compile || \
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
	@find dipeo/diagram_generated_staged -name "*.py" -type f | xargs uv run python -m py_compile || \
		(echo "Python compilation check failed!" && exit 1)
	@echo "Python syntax validation passed!"

# Apply staged changes with full type checking validation
apply: validate-staged
	@echo "Applying staged changes to active directory..."
	@if [ ! -d "dipeo/diagram_generated_staged" ]; then \
		echo "Error: No staged directory found. Run 'make codegen' first."; \
		exit 1; \
	fi
	@echo "Copying staged files to active directory..."
	@cp -r dipeo/diagram_generated_staged/* dipeo/diagram_generated/
	@echo "Staged changes applied successfully!"

# Apply staged changes with syntax checking only (faster)
apply-syntax-only: validate-staged-syntax
	@echo "Applying staged changes to active directory (syntax validation only)..."
	@if [ ! -d "dipeo/diagram_generated_staged" ]; then \
		echo "Error: No staged directory found. Run 'make codegen' first."; \
		exit 1; \
	fi
	@echo "Copying staged files to active directory..."
	@cp -r dipeo/diagram_generated_staged/* dipeo/diagram_generated/
	@echo "Staged changes applied successfully!"

# Test server with staged code before applying (strongest validation)
apply-test: validate-staged-syntax
	@echo "Testing server startup with staged code..."
	@if [ ! -d "dipeo/diagram_generated_staged" ]; then \
		echo "Error: No staged directory found. Run 'make codegen' first."; \
		exit 1; \
	fi
	@echo "Running server validation with staged imports..."
	@uv run python scripts/test_staged_server.py || \
		(echo "Server test failed! Staged code not applied." && exit 1)
	@echo "Server test passed! Applying staged changes..."
	@cp -r dipeo/diagram_generated_staged/* dipeo/diagram_generated/
	@echo "Staged changes applied successfully after server validation!"

backup-generated:
	@echo "Backing up current generated files..."
	@mkdir -p .backups
	@tar -czf .backups/diagram_generated.backup.$$(date +%Y%m%d_%H%M%S).tar.gz dipeo/diagram_generated/
	@echo "Backup created in .backups/"

# Clean staged files only (removes staging directory)
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
	rm -rf .dipeo/logs/*.log 2>/dev/null || true
	rm -rf temp/codegen temp/core temp/specifications 2>/dev/null || true
	@echo "Clean complete."

# Generate database schema documentation
schema-docs:
	@echo "Generating database schema documentation..."
	@python scripts/generate_db_schema_docs.py
	@echo "Schema documentation generated in docs/"

# Documentation anchor management
docs-add-anchors-dry:
	@echo "Previewing anchor additions (dry-run)..."
	@echo ""
	@echo "=== Features Documentation ==="
	@python .claude/skills/maintain-docs/scripts/add_doc_anchors.py docs/features/ --recursive --dry-run
	@echo ""
	@echo "=== Formats Documentation ==="
	@python .claude/skills/maintain-docs/scripts/add_doc_anchors.py docs/formats/ --recursive --dry-run
	@echo ""
	@echo "=== Projects Documentation ==="
	@python .claude/skills/maintain-docs/scripts/add_doc_anchors.py docs/projects/ --recursive --dry-run
	@echo ""
	@echo "To apply these changes, run: make docs-add-anchors"

docs-add-anchors:
	@echo "Adding anchors to documentation..."
	@python .claude/skills/maintain-docs/scripts/add_doc_anchors.py docs/features/ --recursive
	@python .claude/skills/maintain-docs/scripts/add_doc_anchors.py docs/formats/ --recursive
	@python .claude/skills/maintain-docs/scripts/add_doc_anchors.py docs/projects/ --recursive
	@echo "✅ Anchors added. Run 'make docs-validate-anchors' to validate references."

docs-validate-anchors:
	@echo "Validating documentation anchor references in router skills..."
	@python .claude/skills/maintain-docs/scripts/validate_doc_anchors.py

docs-update: docs-add-anchors docs-validate-anchors
	@echo ""
	@echo "✅ Documentation update complete!"
	@echo "  - Anchors added to all docs"
	@echo "  - Router skills validated"
