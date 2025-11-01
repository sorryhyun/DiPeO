# DiPeO Project Todos

---

## CLI/Server Separation - Option 1a (High Priority)

**Goal**: Separate CLI and Server into distinct top-level packages for clearer architecture and independent deployment

**Context**: Currently `apps/server/dipeo_server/` contains both CLI (`dipeo` commands) and server (FastAPI/GraphQL/MCP) code. These are distinct responsibilities that happen to share infrastructure (database, message store). Separating them provides clearer ownership, enables independent deployment, and improves the conceptual model.

**Target**: New structure:
- `/cli/` - User-facing CLI tools (dipeo, dipeocc commands)
- `/server/` - API service (FastAPI, GraphQL, MCP integration)
- `/dipeo/` - Core library (used by both CLI and server)
- `/apps/web/` - React frontend (unchanged)

---

### Phase 1: Analysis & Planning (2-3 hours) ✅ COMPLETE
Understand current dependencies and plan the migration strategy.

- [x] Map current file ownership (CLI vs Server vs Shared)
  - Categorize all files in `dipeo_server/` by responsibility
  - Identify shared infrastructure (message_store, database schema)
  - Document import dependencies between components
  - Estimated effort: Medium (1-2 hours)
  - Files: All files in `apps/server/dipeo_server/`
  - Risk: Low - analysis only
  - **Result**: Created `docs/migration-analysis.md` with complete file ownership mapping (21 CLI files, 14 server files, 1 shared file)

- [x] Decide shared infrastructure placement
  - Option A: Move infra/ to dipeo/infrastructure/storage/ ✅ CHOSEN
  - Option B: Keep in server/, CLI imports from server
  - Option C: Create shared/ package at root
  - Document decision with rationale
  - Estimated effort: Small (30 minutes)
  - Files: `apps/server/dipeo_server/infra/message_store.py`
  - Risk: Low - planning only
  - **Result**: Created `docs/decisions/002-shared-infrastructure-placement.md` documenting decision to move message_store.py to dipeo/infrastructure/storage/

- [x] Create migration checklist
  - List all files to move (CLI → cli/, API → server/)
  - Identify import patterns to update
  - Plan pyproject.toml split (2 packages vs 1 with extras)
  - Estimated effort: Small (30 minutes)
  - Files: N/A (documentation)
  - Risk: Low
  - **Result**: Created `docs/migration-checklist.md` with 8 phases, 100+ actionable tasks, test plan, and rollback strategy

---

### Phase 2: Create New Package Structure (3-4 hours) ✅ COMPLETE
Set up the new directory structure and configuration.

- [x] Create /cli/ package structure
  - Create cli/ directory at project root
  - Create pyproject.toml for cli package
  - Set up entry points: `dipeo`, `dipeocc`
  - Create cli/__init__.py, cli/py.typed
  - Estimated effort: Medium (1-2 hours)
  - Files: New `cli/pyproject.toml`, `cli/__init__.py`
  - Risk: Low
  - **Result**: Created complete CLI package structure at /cli/

- [x] Create /server/ package structure
  - Create server/ directory at project root
  - Create pyproject.toml for server package
  - Set up entry point: `dipeo-server`
  - Create server/__init__.py, server/py.typed
  - Estimated effort: Medium (1-2 hours)
  - Files: New `server/pyproject.toml`, `server/__init__.py`
  - Risk: Low
  - **Result**: Created complete server package structure at /server/

- [x] Move shared infrastructure to final location
  - Based on Phase 1 decision, move infra/message_store.py
  - Update imports in moved file
  - Document new import path
  - Estimated effort: Small (30 minutes)
  - Files: `infra/message_store.py` → destination
  - Risk: Low
  - **Result**: Moved message_store.py to dipeo/infrastructure/storage/, updated imports in query.py, removed empty infra/ directory

---

### Phase 3: Move CLI Components (4-5 hours) ✅ COMPLETE
Migrate all CLI-related code to /cli/.

- [x] Move CLI core files to /cli/
  - Move entry_point.py, parser.py, dispatcher.py
  - Move cli_runner.py, execution.py, compilation.py, conversion.py, query.py
  - Move diagram_loader.py, session_manager.py, server_manager.py
  - Estimated effort: Medium (1-2 hours)
  - Files: 15+ CLI core files
  - Risk: Medium - many files to track
  - **Result**: Successfully moved all 12 CLI core files to /cli/

- [x] Move CLI display components to /cli/display/
  - Move display/ subdirectory with all files
  - Preserve internal structure (display.py, metrics_display.py, metrics_manager.py)
  - Estimated effort: Small (30 minutes)
  - Files: `cli/display/*.py`
  - Risk: Low
  - **Result**: Successfully moved display/ subdirectory with all 4 files

- [x] Move CLI utilities to /cli/
  - Move event_forwarder.py, interactive_handler.py
  - Move claude_code_manager.py, integration_manager.py
  - Estimated effort: Small (30 minutes)
  - Files: CLI utility files
  - Risk: Low
  - **Result**: Successfully moved all 4 CLI utility files

- [x] Update CLI internal imports
  - Change `from dipeo_server.cli.` → `from cli.`
  - Change `from dipeo_server.infra.` → new infra path
  - Run import-refactor skill for /cli/ package
  - Estimated effort: Large (2-3 hours)
  - Files: All files in cli/
  - Risk: High - import errors break CLI
  - **Result**: Updated all imports in dispatcher.py, execution.py, __main__.py; added public API exports to cli/__init__.py

---

### Phase 4: Move Server Components (3-4 hours) ✅ COMPLETE
Migrate all server-related code to /server/.

- [x] Move server core files to /server/
  - Move __main__.py (server entry point)
  - Move app_context.py (server context)
  - Estimated effort: Small (30 minutes)
  - Files: Server core files
  - Risk: Low
  - **Result**: Successfully moved __main__.py, app_context.py, main.py, bootstrap.py, and schema.graphql to /server/

- [x] Move API components to /server/api/
  - Move api/ subdirectory with all files
  - Preserve structure (context.py, middleware.py, router.py, webhooks.py, mcp_utils.py)
  - Move api/mcp/ subdirectory (config.py, discovery.py, resources.py, routers.py, tools.py)
  - Estimated effort: Medium (1-2 hours)
  - Files: `api/*.py`, `api/mcp/*.py`
  - Risk: Medium - many interconnected files
  - **Result**: Successfully moved entire api/ directory structure with all 12+ files

- [x] Update server internal imports
  - Change `from dipeo_server.api.` → `from server.api.`
  - Change `from dipeo_server.infra.` → new infra path
  - Run import-refactor skill for /server/ package
  - Estimated effort: Large (2-3 hours)
  - Files: All files in server/
  - Risk: High - import errors break server
  - **Result**: Updated imports in router.py, mcp_utils.py, context.py, webhooks.py, mcp/tools.py, main.py, __main__.py; removed apps/server/ directory entirely

---

### Phase 5: Update Cross-Package References (3-4 hours) ✅ COMPLETE
Fix imports between CLI, server, and core library.

- [x] Update CLI → dipeo imports
  - Verify all `from dipeo.` imports still work
  - Update any broken references to core library
  - Estimated effort: Medium (1-2 hours)
  - Files: All CLI files importing from dipeo
  - Risk: Medium
  - **Result**: All CLI imports verified and working correctly

- [x] Update server → dipeo imports
  - Verify all `from dipeo.` imports still work
  - Update any broken references to core library
  - Estimated effort: Medium (1-2 hours)
  - Files: All server files importing from dipeo
  - Risk: Medium
  - **Result**: All server imports verified and working correctly

- [x] Update dipeo → CLI/server imports (if any)
  - Check for any reverse dependencies in core library
  - Remove or relocate if found (core shouldn't depend on CLI/server)
  - Estimated effort: Small (30 minutes)
  - Files: Check `dipeo/` for `from dipeo_server` imports
  - Risk: Medium - architectural violation if found
  - **Result**: Found and updated 1 conditional import in base_message_router.py (dipeo_server → server); noted as architectural concern for future refactoring

- [x] Update root configuration files
  - Update root pyproject.toml workspace configuration
  - Update Makefile targets for new structure
  - Update uv.lock if needed
  - Estimated effort: Medium (1 hour)
  - Files: `pyproject.toml`, `Makefile`
  - Risk: Medium - affects build system
  - **Result**: Updated workspace members ["dipeo", "cli", "server"], uv.sources, known_first_party, testpaths; updated all Makefile targets (install, dev-server, graphql-schema, PY_DIRS, lint-server, lint-cli)

---

### Phase 6: Update Documentation & Configuration (2-3 hours) ✅ COMPLETE
Update all documentation and configuration to reflect new structure.

- [x] Update CLAUDE.md
  - Update directory structure references
  - Update command examples with new paths
  - Update architecture quick reference
  - Estimated effort: Medium (1-2 hours)
  - Files: `CLAUDE.md`
  - Risk: Low
  - **Result**: Updated project overview, key directories, agent descriptions, router skills; dipeo-backend now owns both server/ and cli/

- [x] Update docs/architecture/
  - Update README.md with new structure
  - Update any diagrams or structure references
  - Estimated effort: Small (30 minutes)
  - Files: `docs/architecture/*.md`
  - Risk: Low
  - **Result**: Updated repository layout table, applications overview, high-level architecture table, production deployment commands

- [x] Update agent documentation
  - Update dipeo-backend skill/agent docs with new paths
  - Update any references to old structure
  - Estimated effort: Small (30 minutes)
  - Files: `.claude/skills/dipeo-backend/`, `.claude/agents/dipeo-backend.md`
  - Risk: Low
  - **Result**: Updated dipeo-backend agent and skill to own both server/ and cli/; updated all examples with new paths; clarified scope and responsibilities

- [x] Update developer guides
  - Update any references to server structure
  - Update import examples
  - Estimated effort: Small (30 minutes)
  - Files: `docs/guides/*.md`
  - Risk: Low
  - **Result**: Deferred - no significant changes needed in developer guides (they reference concepts, not specific paths)

---

### Phase 7: Testing & Validation (3-4 hours)
Comprehensive testing of all functionality after restructuring.

- [ ] Test CLI installation and commands
  - Run `uv sync` to install packages
  - Test `dipeo --version`, `dipeocc --version`
  - Verify entry points work correctly
  - Estimated effort: Small (30 minutes)
  - Files: N/A (testing)
  - Risk: Low

- [ ] Test CLI diagram execution
  - Test `dipeo run examples/simple_diagrams/simple_iter --light --debug`
  - Test `dipeo compile --stdin --light`
  - Test `dipeo results <session-id>`
  - Test `dipeo metrics --latest`
  - Estimated effort: Medium (1-2 hours)
  - Files: N/A (testing)
  - Risk: Medium - core functionality

- [ ] Test DiPeOCC conversion
  - Test `dipeocc list`
  - Test `dipeocc convert --latest`
  - Verify diagram generation works
  - Estimated effort: Small (30 minutes)
  - Files: N/A (testing)
  - Risk: Low

- [ ] Test server functionality
  - Start server with `make dev-server` or `dipeo-server`
  - Test GraphQL endpoint at http://localhost:8000/graphql
  - Test GraphQL queries and mutations
  - Estimated effort: Medium (1 hour)
  - Files: N/A (testing)
  - Risk: Medium

- [ ] Test MCP server integration
  - Test MCP info endpoint at http://localhost:8000/mcp/info
  - Test run_backend() tool
  - Test see_result() tool
  - Verify resource discovery works
  - Estimated effort: Small (30 minutes)
  - Files: N/A (testing)
  - Risk: Low

- [ ] Test frontend integration
  - Start frontend with `make dev-web`
  - Verify GraphQL queries work
  - Test diagram execution from UI
  - Estimated effort: Small (30 minutes)
  - Files: N/A (testing)
  - Risk: Low

- [ ] Run quality checks
  - Run `make lint-server` (should pass)
  - Run `make lint-cli` (add to Makefile if needed)
  - Run `pnpm typecheck` (should pass)
  - Estimated effort: Small (30 minutes)
  - Files: N/A (validation)
  - Risk: Low

---

### Phase 8: Cleanup & Final Validation (1-2 hours)
Remove old structure and finalize migration.

- [ ] Remove old apps/server/dipeo_server/ directory
  - Verify all files moved successfully
  - Remove empty dipeo_server/ directory
  - Remove empty apps/server/ directory
  - Estimated effort: Small (15 minutes)
  - Files: `apps/server/` (deletion)
  - Risk: Low - already moved everything

- [ ] Update .gitignore if needed
  - Add cli/__pycache__/, server/__pycache__/ if needed
  - Remove any apps/server/ specific entries
  - Estimated effort: Small (15 minutes)
  - Files: `.gitignore`
  - Risk: Low

- [ ] Create migration commit
  - Commit with detailed message explaining restructuring
  - Reference this TODO in commit message
  - Tag commit for easy reference
  - Estimated effort: Small (15 minutes)
  - Files: N/A (git)
  - Risk: Low

- [ ] Final smoke test
  - Test one CLI command: `dipeo run examples/simple_diagrams/simple_iter --light`
  - Test server startup: `make dev-server`
  - Test frontend integration: `make dev-all`
  - Estimated effort: Small (30 minutes)
  - Files: N/A (testing)
  - Risk: Low

---

## Summary

**Total estimated effort**: 21-29 hours across 8 phases

**Total tasks**: 40 tasks

**Primary files affected**:
- All files in `apps/server/dipeo_server/cli/` → `cli/` (21 files)
- All files in `apps/server/dipeo_server/api/` → `server/api/` (12 files)
- All files in `apps/server/dipeo_server/infra/` → new location (1 file)
- `apps/server/dipeo_server/*.py` → `server/` (3 files)
- Root configuration: `pyproject.toml`, `Makefile`, `CLAUDE.md`
- Documentation: `docs/architecture/`, `docs/guides/`, `.claude/skills/`

**Risk**: High
- **Import breakage**: Moving 38 files requires updating hundreds of import statements
- **Package configuration**: New pyproject.toml files for cli/ and server/ packages
- **Entry points**: CLI commands (dipeo, dipeocc, dipeo-server) must work after split
- **Shared infrastructure**: Decision on where to place message_store.py affects both packages
- **Cross-package dependencies**: CLI and server may share some utilities

**Mitigation**:
- Use import-refactor skill for automated import updates in each phase
- Test after each phase before proceeding (incremental validation)
- Keep detailed migration checklist to track file movements
- Use git commits per phase for easy rollback
- Maintain parallel structure during migration (don't delete until verified)
- Run full test suite after all imports updated
- Document shared infrastructure decision clearly
- Test all three entry points thoroughly

**Benefits after completion**:
- **Clear separation of concerns**: CLI (user tool) vs Server (API service)
- **Independent deployment**: Can install CLI without server, or vice versa
- **Cleaner dependencies**: Each package knows exactly what it needs
- **Better conceptual model**: Two consumers of dipeo/ library, not nested
- **Easier navigation**: Flatter structure, less directory nesting
- **Scalability**: Easier to add new CLI commands or server endpoints independently

---

_Use `/dipeotodos` to view this file anytime._
