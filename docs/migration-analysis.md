# CLI/Server Separation - File Ownership Analysis

Generated: 2025-11-01

## Current Structure

```
apps/server/
├── dipeo_server/           # Combined package (both CLI and Server)
│   ├── cli/               # CLI code
│   ├── api/               # Server API code
│   ├── infra/             # Shared infrastructure
│   ├── __main__.py        # Server entry point
│   ├── app_context.py     # Server container setup
│   └── py.typed
├── main.py                 # FastAPI server app
├── bootstrap.py            # Server bootstrap/wiring
└── pyproject.toml          # Single package config

Entry points (in pyproject.toml):
- dipeo-server → dipeo_server.__main__:main
- dipeo → dipeo_server.cli.entry_point:main
- dipeocc → dipeo_server.cli.entry_point:dipeocc_main
```

## File Ownership Mapping

### CLI Components (21 files) → `/cli/`

**Core CLI files:**
- `cli/entry_point.py` - Main CLI entry point (dipeo/dipeocc commands)
- `cli/parser.py` - Command-line argument parsing
- `cli/dispatcher.py` - Command dispatching logic
- `cli/cli_runner.py` - CLI execution orchestration
- `cli/__main__.py` - Python module entry point

**Command implementations:**
- `cli/commands/execution.py` - Diagram execution via CLI
- `cli/commands/compilation.py` - Diagram compilation via CLI
- `cli/commands/conversion.py` - DiPeOCC conversion via CLI
- `cli/commands/query.py` - Query/results commands

**CLI utilities:**
- `cli/diagram_loader.py` - Load diagrams from filesystem
- `cli/session_manager.py` - CLI session management
- `cli/server_manager.py` - Start/stop server from CLI
- `cli/event_forwarder.py` - Forward CLI events
- `cli/interactive_handler.py` - Interactive CLI prompts
- `cli/claude_code_manager.py` - Claude Code integration
- `cli/integration_manager.py` - Integration management

**CLI display (4 files):**
- `cli/display/__init__.py`
- `cli/display/display.py` - Terminal display logic
- `cli/display/metrics_display.py` - Metrics formatting
- `cli/display/metrics_manager.py` - Metrics collection

### Server Components (12 files) → `/server/`

**Server core:**
- `__main__.py` - Server entry point (imports main.py)
- `app_context.py` - Server-specific container initialization
- `main.py` - FastAPI application (currently at apps/server/main.py)
- `bootstrap.py` - Dependency injection wiring (currently at apps/server/bootstrap.py)

**API layer (8 files):**
- `api/__init__.py`
- `api/router.py` - GraphQL router setup
- `api/context.py` - GraphQL context
- `api/middleware.py` - FastAPI middleware
- `api/webhooks.py` - Webhook endpoints
- `api/mcp_utils.py` - MCP utility functions

**MCP integration (6 files):**
- `api/mcp/__init__.py`
- `api/mcp/config.py` - MCP configuration
- `api/mcp/discovery.py` - Resource discovery
- `api/mcp/resources.py` - MCP resources
- `api/mcp/routers.py` - MCP routes
- `api/mcp/tools.py` - MCP tools

### Shared Infrastructure (1 file) → Decision needed

**Database/Persistence:**
- `infra/message_store.py` - Message persistence (SQLite)
  - Used by: Both CLI (for storing execution results) and Server (for GraphQL queries)
  - Options:
    1. Move to `/dipeo/infrastructure/storage/message_store.py` (preferred)
    2. Keep in `/server/infra/`, CLI imports from server
    3. Create `/shared/` package at root

## Import Dependency Analysis

### CLI → dipeo (Core Library)
```python
# Heavy usage of core library
from dipeo.application.bootstrap import Container, init_resources
from dipeo.application.diagram import DiagramService
from dipeo.application.execution import ExecutionService
from dipeo.domain.diagram import Diagram
from dipeo.infrastructure.logging_config import setup_logging
```

### CLI → Server Infrastructure
```python
# Currently imports from shared infra
from dipeo_server.infra.message_store import MessageStore
```

### Server → dipeo (Core Library)
```python
# Heavy usage of core library
from dipeo.application.bootstrap import Container, init_resources
from dipeo.application.graphql import schema
from dipeo.infrastructure.logging_config import setup_logging
```

### Server → Server Infrastructure
```python
# Internal imports
from dipeo_server.api.router import setup_routes
from dipeo_server.api.middleware import setup_middleware
from dipeo_server.app_context import initialize_container_async
from dipeo_server.infra.message_store import MessageStore
```

## Package Configuration Analysis

### Current: Single Package
```toml
[project]
name = "dipeo-server"
dependencies = []  # Root manages all deps

[project.scripts]
dipeo-server = "dipeo_server.__main__:main"
dipeo = "dipeo_server.cli.entry_point:main"
dipeocc = "dipeo_server.cli.entry_point:dipeocc_main"
```

### Proposed: Two Packages

**Option A: Separate packages with root workspace**
```
/cli/pyproject.toml
/server/pyproject.toml
/pyproject.toml (workspace root)
```

**Option B: Single package with extras**
```toml
[project]
name = "dipeo"

[project.optional-dependencies]
cli = [...]
server = [...]
```

Recommendation: **Option A** for clearer separation

## Shared Infrastructure Decision

### Recommendation: Move to `/dipeo/infrastructure/storage/`

**Rationale:**
1. **Architectural consistency**: Message store is infrastructure, belongs in core library
2. **Dependency direction**: Both CLI and server depend on dipeo, not each other
3. **Reusability**: Future consumers (tests, tools) can access without server dependency
4. **Conceptual model**: Message persistence is a core capability, not server-specific

**New location:**
- `/dipeo/infrastructure/storage/message_store.py`

**Import path:**
```python
from dipeo.infrastructure.storage.message_store import MessageStore
```

**Alternative considered:**
- Keep in `/server/infra/`, CLI imports from server
  - ❌ Creates dependency from CLI → server (wrong direction)
  - ❌ Can't use CLI without installing server package

## Migration Checklist

### Phase 1: Create Structure
- [ ] Create `/cli/` package structure
- [ ] Create `/server/` package structure
- [ ] Move shared infra to `/dipeo/infrastructure/storage/`

### Phase 2: Move CLI Files (21 files)
- [ ] Move `cli/` directory → `/cli/`
- [ ] Update internal imports (`dipeo_server.cli` → `cli`)
- [ ] Update infra imports (`dipeo_server.infra` → `dipeo.infrastructure.storage`)

### Phase 3: Move Server Files (12 files + 2 external)
- [ ] Move `api/` directory → `/server/api/`
- [ ] Move `__main__.py`, `app_context.py` → `/server/`
- [ ] Move `main.py` → `/server/main.py`
- [ ] Move `bootstrap.py` → `/server/bootstrap.py`
- [ ] Update internal imports (`dipeo_server.api` → `server.api`)
- [ ] Update infra imports (`dipeo_server.infra` → `dipeo.infrastructure.storage`)

### Phase 4: Configuration
- [ ] Create `/cli/pyproject.toml` with dipeo entry point
- [ ] Create `/server/pyproject.toml` with dipeo-server entry point
- [ ] Update root `pyproject.toml` workspace configuration
- [ ] Update `Makefile` targets

### Phase 5: Documentation
- [ ] Update CLAUDE.md with new structure
- [ ] Update docs/architecture/README.md
- [ ] Update agent documentation (.claude/skills/dipeo-backend/)

### Phase 6: Testing
- [ ] Test CLI: `dipeo run examples/simple_diagrams/simple_iter --light`
- [ ] Test server: `make dev-server`
- [ ] Test DiPeOCC: `dipeocc convert --latest`
- [ ] Test MCP: curl http://localhost:8000/mcp/info

### Phase 7: Cleanup
- [ ] Remove `apps/server/dipeo_server/` directory
- [ ] Remove empty `apps/server/` directory
- [ ] Update .gitignore

## Risk Assessment

### High Risk Areas
1. **Import breakage** - 38 files moving, hundreds of imports to update
2. **Entry points** - Three commands must work: dipeo, dipeocc, dipeo-server
3. **Shared infrastructure** - Message store must be accessible to both packages
4. **Package dependencies** - CLI and server must have correct deps

### Mitigation Strategies
1. Use `import-refactor` skill for automated import updates
2. Test after each phase before proceeding
3. Keep detailed file movement log
4. Use git commits per phase for easy rollback
5. Don't delete old files until verified working

## Benefits After Migration

1. **Clear separation of concerns**: CLI (user tool) vs Server (API service)
2. **Independent deployment**: Install CLI without server, or vice versa
3. **Cleaner dependencies**: Each package knows exactly what it needs
4. **Better conceptual model**: Two consumers of dipeo library, not nested
5. **Easier navigation**: Flatter structure, less directory nesting
6. **Scalability**: Easier to add new CLI commands or server endpoints

## Total Effort Estimate

- File mapping: ✅ Complete (2 hours)
- Shared infra decision: Pending (30 minutes)
- Migration execution: 19-27 hours remaining
- **Total: 21-29 hours**
