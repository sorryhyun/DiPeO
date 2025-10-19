# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this DiPeO repository.

## Project Overview

DiPeO is a monorepo for building and executing AI-powered agent workflows through visual programming:
- **Frontend** (apps/web/): React-based visual diagram editor
- **Backend** (apps/server/): FastAPI server with GraphQL API
- **CLI** (apps/server/src/dipeo_server/cli/): Command-line tool for running diagrams (`dipeo` command)

## Essential Commands

### Setup & Development
```bash
make install          # Install dependencies (auto-installs uv)
make dev-all          # Start frontend + backend
make dev-web          # Frontend only (port 3000)
make dev-server       # Backend only (port 8000)
```

### Running Diagrams
```bash
# Synchronous execution (wait for completion)
dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=40 --timing # simple_iter_cc for claude code adapter diagram
dipeo run [diagram] --input-data '{"key": "value"}' --light --debug

# Asynchronous execution (background)
dipeo run examples/simple_diagrams/simple_iter --light --background --timeout=40
# Output: {"session_id": "exec_...", "status": "started"}

# Check execution status and results
dipeo results exec_9ebb3df7180a4a7383079680c28c6028
# Output: Full execution status with results, LLM usage, etc.

# Profile executions
dipeo metrics --latest --breakdown  # Profile latest execution
```

### Export to Python
```bash
dipeo export <diagram> <output.py> --light  # Export diagram to standalone Python script
dipeo export examples/simple_diagrams/simple_iter.light.yaml output.py --light
```
See [Diagram-to-Python Export Guide](docs/features/diagram-to-python-export.md)

### Compile and Push (for MCP)
```bash
# Validate from file
dipeo compile my_diagram.light.yaml --light

# Validate from stdin (LLM-friendly)
echo '<diagram-content>' | dipeo compile --stdin --light

# Compile and push to MCP directory (from file)
dipeo compile my_diagram.light.yaml --light --push-as my_workflow

# Compile and push from stdin (LLM-friendly workflow)
echo '<diagram-content>' | dipeo compile --stdin --light --push-as my_workflow

# Custom target directory
dipeo compile --stdin --light --push-as my_workflow --target-dir /custom/path
```

**Benefits:**
- **Safe Upload**: Only valid diagrams are pushed
- **No File Persistence**: LLMs can validate and push diagrams from text without filesystem access
- **Automatic MCP Integration**: Pushed diagrams immediately available via `dipeo_run`

See [MCP Server Integration](docs/features/mcp-server-integration.md#3-uploading-diagrams-for-mcp-access)

### Code Generation
```bash
cd dipeo/models && pnpm build      # Build TypeScript specs
make codegen                        # Generate code (→ staged/)
make diff-staged                    # Review changes
make apply-test                     # Apply with validation
make graphql-schema                 # Update GraphQL types
```

See [Code Generation Guide](docs/projects/code-generation-guide.md)

### DiPeOCC (Claude Code Session Conversion)
```bash
dipeocc list                    # List recent sessions
dipeocc convert --latest        # Convert latest
dipeocc convert {session-id}    # Convert specific
```
See [DiPeOCC Guide](docs/projects/dipeocc-guide.md)

### MCP Server (Expose DiPeO diagrams as MCP tools)
```bash
make dev-server                 # Start DiPeO server (port 8000)
ngrok http 8000                 # Expose via HTTPS (requires ngrok auth token)
# Access: https://your-url.ngrok-free.app/mcp/info
```
See [MCP Server Integration](docs/features/mcp-server-integration.md)

### Quality
```bash
make lint-server        # Lint Python
make lint-web           # Lint TypeScript
pnpm typecheck          # TypeScript checking
make format             # Format Python
```

## Claude Code Subagents

DiPeO uses specialized subagents for complex tasks.
Run agents in parallel when possible. [Agent docs](docs/agents/index.md)

## Claude Code Skills

DiPeO provides specialized skills for routine code quality and project management tasks. Access skills via the Skill tool.

### todo-manage Skill

**When to use**: For comprehensive TODO list management when working on multi-phase projects, complex migrations, or when planning feature implementations that require structured task tracking.

**Use the `todo-manage` skill when:**
- Planning multi-phase projects (3+ phases or 10+ tasks)
- Organizing complex migrations or refactoring work
- Breaking down large feature requests into structured task lists
- User explicitly requests comprehensive TODO planning
- Need to create organized, phase-based task breakdown with estimates

**Examples:**

<example>
Context: User requests a major migration that requires multiple coordinated steps
user: "We need to migrate from legacy MCP to SDK-only implementation"
assistant: "I'll use the todo-manage skill to create a comprehensive, phase-based TODO list for this migration."
<commentary>Use todo-manage for complex migrations requiring structured planning with phases, estimates, and dependencies.</commentary>
</example>

<example>
Context: User wants to implement a large feature with many components
user: "Add authentication system with OAuth, JWT, API keys, and role-based access control"
assistant: "Let me use the todo-manage skill to break this down into a comprehensive TODO list organized by implementation phases."
<commentary>Use todo-manage for large feature implementations that need structured task breakdown.</commentary>
</example>

<example>
Context: User wants comprehensive project planning
user: "Create a TODO list for implementing the new diagram export system"
assistant: "I'll use the todo-manage skill to create a detailed, phase-organized TODO list with effort estimates and dependencies."
<commentary>Use todo-manage when user explicitly requests TODO planning or when project complexity warrants structured task management.</commentary>
</example>

**Access TODO list**: Use `/dipeotodos` slash command to view current TODO.md

**Don't use todo-manage for:**
- Simple, single-task changes (use regular TodoWrite tool instead)
- Quick bug fixes or minor updates
- When you just need to mark existing TODOs as complete

### Other Skills

- **clean-comments**: Remove unnecessary comments while preserving valuable ones
- **import-refactor**: Update imports after moving/renaming files
- **maintain-docs**: Keep documentation current with implementation
- **separate-monolithic-python**: Break large Python files (>500 LOC) into modules

**Note**: TypeScript type fixing is handled by the **dipeo-frontend-dev** agent.

See `.claude/skills/` for detailed skill documentation.

## Architecture Quick Reference

### Key Concepts
- **Code Generation**: TypeScript specs → IR → Python
- **Avoid editing** `dipeo/diagram_generated/` directly - modify TypeScript specs instead
- **Diagram Compilation**: 6-phase pipeline (Validation → Transformation → Resolution → Edge Building → Optimization → Assembly)
- **Configuration-Driven**: HandleSpec tables, field mappings - no if-elif chains
- **Strategy Pattern**: Consistent parser → transformer → serializer → strategy structure
- **GraphQL**: 3-tier architecture (Generated → Application → Execution)
- **Service Registry**: EnhancedServiceRegistry with type categorization, audit trails
- **Event System**: Unified EventBus protocol
- **Output Pattern**: Envelope pattern via EnvelopeFactory

### Key Directories
- `/apps/server/` - FastAPI backend + CLI
- `/apps/web/` - React frontend
- `/dipeo/` - Core Python (application/domain/infrastructure)
- `/dipeo/models/src/` - TypeScript specs (source of truth)
- `/dipeo/diagram_generated/` - Generated code (don't edit)

See [Overall Architecture](docs/architecture/README.md) for complete details.

## Adding New Features

### New Node Types
1. Create spec in `/dipeo/models/src/nodes/`
2. Build: `cd dipeo/models && pnpm build`
3. Generate: `make codegen` → `make diff-staged` → `make apply-test`
4. Configure handles in `/dipeo/domain/diagram/utils/shared_components.py` (HANDLE_SPECS)
5. Add field mappings if needed in `/dipeo/domain/diagram/utils/node_field_mapper.py` (FIELD_MAPPINGS)
6. Create handler in `/dipeo/application/execution/handlers/`
7. Update schema: `make graphql-schema`

See [Developer Guide](docs/guides/developer-guide-diagrams.md) for detailed instructions.

### New Diagram Formats
1. Create strategy in `/dipeo/domain/diagram/strategies/my_format/`
2. Implement: `parser.py`, `transformer.py`, `serializer.py`, `strategy.py`
3. Follow existing patterns (see `light/` or `readable/`)
4. Register strategy in format registry

See [Developer Guide](docs/guides/developer-guide-diagrams.md#adding-new-diagram-formats) for details.

### GraphQL Operations
1. Add definition in `/dipeo/models/src/frontend/query-definitions/`
2. Follow codegen workflow above
3. See [GraphQL Layer](docs/architecture/graphql-layer.md)

### Other Changes
- **API changes**: Modify schema → `make graphql-schema`
- **UI changes**: Work in `/apps/web/src/`
- **Compilation phases**: Create phase class implementing PhaseInterface (see [Diagram Compilation](docs/architecture/diagram-compilation.md))

## Important Notes

- **Python 3.13+** required
- **uv** for Python, **pnpm** for JavaScript (not npm/yarn)
- Default LLM: `gpt-5-nano-2025-08-07`
- Backend: port 8000, Frontend: port 3000
- Debug with `--debug` flag, check `.dipeo/logs/cli.log`
- Formal test suite under development

## Common Issues & Solutions

| Issue | Solution | Documentation |
|-------|----------|-------------|
| Import errors | `make install` (uv auto-manages env) | |
| Generated code sync | Run codegen workflow | |
| TypeScript errors | `make graphql-schema` | |
| Need debugging | Add `--debug`, check `.dipeo/logs/` | |
| Claude Code sessions | Use `dipeocc convert` | |

## Quick Debug Reference

- **Run diagrams**: `dipeo run [diagram] --light --debug`
- **Monitor UI**: `http://localhost:3000/?monitor=true`
- **GraphQL playground**: `http://localhost:8000/graphql`
- **Logs**: `.dipeo/logs/cli.log` for detailed output

---

**For comprehensive documentation**, see [Documentation Index](docs/index.md) 
