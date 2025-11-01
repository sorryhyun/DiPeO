# CLI/Server Separation - Detailed Migration Checklist

**Date**: 2025-11-01
**Reference**: TODO.md (CLI/Server Separation - Option 1a)

## Pre-Migration Verification

- [x] File ownership mapped (docs/migration-analysis.md)
- [x] Shared infrastructure decision made (docs/decisions/002-shared-infrastructure-placement.md)
- [ ] Git working directory is clean
- [ ] All tests passing
- [ ] Create migration branch: `git checkout -b migration/cli-server-separation`

## Phase 1: Move Shared Infrastructure

### 1.1 Move message_store.py to core library
- [ ] Move `apps/server/dipeo_server/infra/message_store.py` → `dipeo/infrastructure/storage/message_store.py`
- [ ] Move `apps/server/dipeo_server/infra/__init__.py` (if needed for exports)
- [ ] Update `dipeo/infrastructure/storage/__init__.py` to export MessageStore

### 1.2 Update imports in existing code
- [ ] Search for `from dipeo_server.infra.message_store import MessageStore` in all files
- [ ] Replace with `from dipeo.infrastructure.storage.message_store import MessageStore`
- [ ] Files likely affected:
  - CLI files (search in `apps/server/dipeo_server/cli/`)
  - Server files (search in `apps/server/dipeo_server/api/`)
  - Bootstrap files (`apps/server/bootstrap.py`, `apps/server/dipeo_server/app_context.py`)

### 1.3 Test shared infrastructure move
- [ ] Run `make lint-server` (should pass)
- [ ] Run `dipeo run examples/simple_diagrams/simple_iter --light --debug` (should work)
- [ ] Commit: `git commit -m "refactor: move message_store to core library"`

## Phase 2: Create New Package Structures

### 2.1 Create /cli/ package
```bash
mkdir -p cli
touch cli/__init__.py
touch cli/py.typed
```

- [ ] Create `cli/` directory at project root
- [ ] Create `cli/__init__.py`
- [ ] Create `cli/py.typed`
- [ ] Create `cli/pyproject.toml`:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "dipeo-cli"
version = "1.0.0"
description = "DiPeO Command-Line Interface"
requires-python = ">=3.13"
dependencies = []  # Dependencies managed by root pyproject.toml

[project.scripts]
dipeo = "cli.entry_point:main"
dipeocc = "cli.entry_point:dipeocc_main"

[tool.hatch.build.targets.wheel]
packages = ["cli"]
```

### 2.2 Create /server/ package
```bash
mkdir -p server
touch server/__init__.py
touch server/py.typed
```

- [ ] Create `server/` directory at project root
- [ ] Create `server/__init__.py`
- [ ] Create `server/py.typed`
- [ ] Create `server/pyproject.toml`:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "dipeo-server"
version = "1.0.0"
description = "DiPeO Backend API Server"
requires-python = ">=3.13"
dependencies = []  # Dependencies managed by root pyproject.toml

[project.scripts]
dipeo-server = "server.__main__:main"

[tool.hatch.build.targets.wheel]
packages = ["server"]
```

### 2.3 Test package structure
- [ ] Verify directories created: `ls -la cli/ server/`
- [ ] Commit: `git commit -m "feat: create cli and server package structures"`

## Phase 3: Move CLI Components (21 files)

### 3.1 Move CLI core files
```bash
# Use git mv to preserve history
git mv apps/server/dipeo_server/cli/*.py cli/
# Except __init__.py and __main__.py for now
```

- [ ] Move `cli/entry_point.py`
- [ ] Move `cli/parser.py`
- [ ] Move `cli/dispatcher.py`
- [ ] Move `cli/cli_runner.py`
- [ ] Move `cli/execution.py`
- [ ] Move `cli/compilation.py`
- [ ] Move `cli/conversion.py`
- [ ] Move `cli/query.py`

### 3.2 Move CLI utility files
- [ ] Move `cli/diagram_loader.py`
- [ ] Move `cli/session_manager.py`
- [ ] Move `cli/server_manager.py`
- [ ] Move `cli/event_forwarder.py`
- [ ] Move `cli/interactive_handler.py`
- [ ] Move `cli/claude_code_manager.py`
- [ ] Move `cli/integration_manager.py`

### 3.3 Move CLI display subdirectory
```bash
git mv apps/server/dipeo_server/cli/display cli/
```

- [ ] Move `cli/display/` directory (preserve structure)
- [ ] Verify all 4 files moved:
  - `display/__init__.py`
  - `display/display.py`
  - `display/metrics_display.py`
  - `display/metrics_manager.py`

### 3.4 Update CLI internal imports
Use the import-refactor skill:
```
import-refactor --old-path "dipeo_server.cli" --new-path "cli" --directory cli/
```

- [ ] Replace `from dipeo_server.cli.` → `from cli.`
- [ ] Replace `from dipeo_server.infra.` → `from dipeo.infrastructure.storage.`
- [ ] Manual verification of complex imports
- [ ] Check relative imports (`.dispatcher`, `.parser`, etc.)

### 3.5 Test CLI move
- [ ] Run `python -m cli.entry_point --help` (should show help)
- [ ] Commit: `git commit -m "refactor: move CLI code to /cli/ package"`

## Phase 4: Move Server Components (14 files)

### 4.1 Move server core files
```bash
git mv apps/server/dipeo_server/__main__.py server/
git mv apps/server/dipeo_server/app_context.py server/
git mv apps/server/main.py server/
git mv apps/server/bootstrap.py server/
```

- [ ] Move `__main__.py` → `server/__main__.py`
- [ ] Move `app_context.py` → `server/app_context.py`
- [ ] Move `main.py` → `server/main.py`
- [ ] Move `bootstrap.py` → `server/bootstrap.py`

### 4.2 Move API subdirectory
```bash
git mv apps/server/dipeo_server/api server/
```

- [ ] Move `api/` directory (preserve structure)
- [ ] Verify 8 files moved (including mcp/ subdirectory):
  - `api/__init__.py`
  - `api/router.py`
  - `api/context.py`
  - `api/middleware.py`
  - `api/webhooks.py`
  - `api/mcp_utils.py`
  - `api/mcp/*.py` (6 files)

### 4.3 Update server internal imports
Use the import-refactor skill:
```
import-refactor --old-path "dipeo_server.api" --new-path "server.api" --directory server/
import-refactor --old-path "dipeo_server.app_context" --new-path "server.app_context" --directory server/
```

- [ ] Replace `from dipeo_server.api.` → `from server.api.`
- [ ] Replace `from dipeo_server.app_context` → `from server.app_context`
- [ ] Replace `from dipeo_server.infra.` → `from dipeo.infrastructure.storage.`
- [ ] Update `server/__main__.py` to import from `server.main`
- [ ] Update `server/main.py` imports

### 4.4 Test server move
- [ ] Run `python -m server.__main__ --help` or check server starts
- [ ] Commit: `git commit -m "refactor: move server code to /server/ package"`

## Phase 5: Update Cross-Package References

### 5.1 Update CLI imports from dipeo
- [ ] Search CLI for `from dipeo.` imports
- [ ] Verify all still work (should be fine, no changes needed)

### 5.2 Update server imports from dipeo
- [ ] Search server for `from dipeo.` imports
- [ ] Verify all still work (should be fine, no changes needed)

### 5.3 Check for reverse dependencies
- [ ] Search dipeo/ for `from dipeo_server` (should be none)
- [ ] Search dipeo/ for `from apps.server` (should be none)
- [ ] If found, remove or relocate (architectural violation)

### 5.4 Update root configuration
- [ ] Update root `pyproject.toml` to include cli and server in workspace
```toml
[tool.hatch.build.targets.wheel]
packages = ["dipeo", "cli", "server"]
```

- [ ] Update `Makefile`:
  - Add `lint-cli` target
  - Update paths in existing targets
  - Update `dev-server` to use new server location

- [ ] Run `uv sync` to update dependencies

### 5.5 Test cross-package references
- [ ] Test CLI can access dipeo library
- [ ] Test server can access dipeo library
- [ ] No circular dependencies detected
- [ ] Commit: `git commit -m "build: update package configuration for separation"`

## Phase 6: Update Documentation

### 6.1 Update CLAUDE.md
- [ ] Update directory structure section:
```markdown
### Key Directories
- `/cli/` - Command-line interface (dipeo, dipeocc)
- `/server/` - FastAPI backend + GraphQL API
- `/dipeo/` - Core Python library
- `/apps/web/` - React frontend
- `/dipeo/models/src/` - TypeScript specs
```

- [ ] Update command examples (should still work)
- [ ] Update "Working with Specialized Agents" section if needed

### 6.2 Update docs/architecture/README.md
- [ ] Update architecture overview with new structure
- [ ] Add diagram showing CLI and server as consumers of dipeo library

### 6.3 Update agent documentation
- [ ] Update `.claude/skills/dipeo-backend/SKILL.md` with new paths
- [ ] Update `docs/agents/dipeo-backend.md` with new structure
- [ ] Update references to `apps/server/dipeo_server/` → `/cli/` or `/server/`

### 6.4 Update developer guides
- [ ] Search `docs/guides/` for `apps/server/dipeo_server/` references
- [ ] Update import examples in guides
- [ ] Update any CLI/server-specific documentation

### 6.5 Commit documentation updates
- [ ] Commit: `git commit -m "docs: update for CLI/server separation"`

## Phase 7: Testing & Validation

### 7.1 Test CLI installation
- [ ] Run `uv sync` to install packages
- [ ] Test `dipeo --version` (should work)
- [ ] Test `dipeocc --version` (should work)
- [ ] Verify entry points work correctly

### 7.2 Test CLI diagram execution
- [ ] Test: `dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=40`
- [ ] Verify execution completes successfully
- [ ] Check logs in `.dipeo/logs/cli.log`

### 7.3 Test CLI other commands
- [ ] Test: `dipeo compile --stdin --light` (with sample diagram)
- [ ] Test: `dipeo results <session-id>` (from previous execution)
- [ ] Test: `dipeo metrics --latest --breakdown`
- [ ] Test: `dipeo export examples/simple_diagrams/simple_iter.light.yaml output.py --light`

### 7.4 Test DiPeOCC conversion
- [ ] Test: `dipeocc list`
- [ ] Test: `dipeocc convert --latest` (if sessions available)
- [ ] Verify diagram generation works

### 7.5 Test server functionality
- [ ] Start server: `make dev-server` or `dipeo-server`
- [ ] Verify server starts on port 8000
- [ ] Check health endpoint: `curl http://localhost:8000/health`
- [ ] Test GraphQL endpoint: `curl http://localhost:8000/graphql`

### 7.6 Test MCP server integration
- [ ] Verify server running
- [ ] Test: `curl http://localhost:8000/mcp/info`
- [ ] Test MCP tools (run_backend, see_result) if possible
- [ ] Verify resource discovery works

### 7.7 Test frontend integration
- [ ] Start frontend: `make dev-web`
- [ ] Verify frontend connects to GraphQL API
- [ ] Test diagram execution from UI
- [ ] Check browser console for errors

### 7.8 Run quality checks
- [ ] Run `make lint-server` (should pass)
- [ ] Run `make lint-cli` (add to Makefile if needed)
- [ ] Run `pnpm typecheck` (should pass)
- [ ] Run `make format` (format Python code)

### 7.9 Integration test
- [ ] Run full stack: `make dev-all`
- [ ] Execute diagram from CLI
- [ ] View results in UI
- [ ] Verify all components communicate correctly

### 7.10 Document test results
- [ ] Create test report in `docs/migration-test-results.md`
- [ ] Note any issues found
- [ ] Commit: `git commit -m "test: validate CLI/server separation"`

## Phase 8: Cleanup & Final Validation

### 8.1 Remove old directory structure
⚠️ **ONLY after all tests pass**

- [ ] Verify all files moved successfully
- [ ] Check for any remaining files in `apps/server/dipeo_server/`
- [ ] Remove `apps/server/dipeo_server/` directory
```bash
git rm -r apps/server/dipeo_server/
```

- [ ] Remove empty `apps/server/` directory if no other files
```bash
git rm -r apps/server/
```

### 8.2 Update .gitignore
- [ ] Add `cli/__pycache__/` (if not already covered by `**/__pycache__/`)
- [ ] Add `server/__pycache__/` (if not already covered)
- [ ] Remove any `apps/server/` specific entries

### 8.3 Final verification
- [ ] Clean install: Remove `.venv`, run `uv sync`
- [ ] Test one CLI command: `dipeo run examples/simple_diagrams/simple_iter --light`
- [ ] Test server startup: `make dev-server`
- [ ] Test frontend integration: `make dev-all`

### 8.4 Create migration commit
- [ ] Review all changes: `git status`
- [ ] Create comprehensive commit message:
```
refactor: separate CLI and server into distinct packages

BREAKING CHANGE: Package structure reorganized

- Moved CLI code from apps/server/dipeo_server/cli/ to /cli/
- Moved server code from apps/server/dipeo_server/ to /server/
- Moved shared infrastructure to /dipeo/infrastructure/storage/
- Updated all imports and entry points
- Separated package configurations (cli/pyproject.toml, server/pyproject.toml)

Benefits:
- Clear separation of concerns (CLI vs Server)
- Independent deployment options
- Cleaner dependency management
- Better conceptual model (two consumers of dipeo library)

Migration guide: docs/migration-analysis.md
Decision records: docs/decisions/002-shared-infrastructure-placement.md

Total files moved: 38
- CLI: 21 files
- Server: 14 files
- Shared: 1 file (message_store.py)

Tested:
- ✅ CLI commands (dipeo, dipeocc)
- ✅ Server startup and GraphQL API
- ✅ MCP integration
- ✅ Frontend integration
- ✅ All quality checks passing

Fixes: Reference TODO.md CLI/Server Separation - Option 1a
```

- [ ] Commit: `git commit -m "..." --no-verify` (skip hooks if needed)
- [ ] Tag commit: `git tag -a v1.0.0-cli-server-separation -m "CLI/Server separation complete"`

### 8.5 Final smoke test
- [ ] Fresh clone in temp directory
- [ ] Run `uv sync`
- [ ] Test CLI: `dipeo run examples/simple_diagrams/simple_iter --light`
- [ ] Test server: `make dev-server` in background
- [ ] Test UI: `make dev-web`
- [ ] Verify end-to-end workflow

## Post-Migration Tasks

### Documentation
- [ ] Update README.md if needed
- [ ] Create migration announcement/changelog entry
- [ ] Update any external documentation

### Monitoring
- [ ] Monitor for import errors in first few days
- [ ] Check CI/CD pipeline if applicable
- [ ] Watch for user-reported issues

### Follow-up
- [ ] Consider adding automated migration tests
- [ ] Update developer onboarding docs
- [ ] Share lessons learned with team

## Rollback Plan

If critical issues discovered:

1. Revert to commit before Phase 2: `git reset --hard <commit-before-migration>`
2. Or revert individual commits in reverse order
3. Critical files to restore:
   - `apps/server/dipeo_server/` (all files)
   - Entry points in `apps/server/pyproject.toml`

## Notes

- Total estimated time: 21-29 hours
- Phases can be done incrementally with commits after each
- Test after each phase before proceeding
- Keep detailed notes of any issues encountered
- Use `git mv` to preserve file history
- Use import-refactor skill for bulk import updates

## Completion

- [ ] All phases complete
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Migration branch merged to dev
- [ ] Tag created
- [ ] Team notified
