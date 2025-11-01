# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this DiPeO repository.

## Project Overview

DiPeO is a monorepo for building and executing AI-powered agent workflows through visual programming:
- **Frontend** (apps/web/): React-based visual diagram editor
- **Server** (server/): FastAPI server with GraphQL API
- **CLI** (cli/): Command-line tools for running diagrams (`dipeo` and `dipeocc` commands)
- **Core Library** (dipeo/): Shared domain logic, execution engine, and infrastructure

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
dipeo compile my_diagram.light.yaml --light              # Validate
dipeo compile --stdin --light --push-as my_workflow      # Validate + push to MCP
# Also supports: --target-dir for custom location
```
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

### Documentation
```bash
make schema-docs        # Generate database schema docs
# Generates docs/database-schema.md (markdown) and docs/database-schema.sql (SQL reference)

python scripts/generate_light_diagram_schema.py  # Generate JSON Schema for light diagram format
# Reads auto-generated node schemas from diagram_generated/schemas/nodes/
```

## Working with Specialized Agents

**IMPORTANT**: Delegate domain-specific work to specialized agents. They have deep context and expertise.

### When to Delegate

**Always delegate when:**
- Task touches multiple files in a domain (handlers, CLI commands, React components)
- Debugging domain-specific issues (execution failures, codegen errors, type errors)
- Implementing new features in a domain (new node types, CLI commands, UI components)
- Exploring unfamiliar code areas

**Handle directly only when:**
- Single-file trivial edits (fixing typos, updating comments)
- Reading/searching for specific information
- Running simple commands

### Available Agents (Run in Parallel)

**Core Development:**
- **dipeo-package-maintainer** → /dipeo/ runtime (handlers, resolvers, EventBus, ServiceRegistry, domain models)
- **dipeo-backend** → /server/ + /cli/ (FastAPI server, CLI tools, database, MCP server)
- **dipeo-codegen-pipeline** → TypeScript specs → IR → Python/GraphQL generation
- **dipeo-frontend-dev** → React UI, visual editor, GraphQL hooks, type errors

**Specialized:**
- **codebase-auditor** → Security, performance, quality analysis
- **dipeocc-converter** → Claude Code session → DiPeO diagram conversion
- **code-polisher** → File separation, comment cleanup, import refactoring
- **codebase-qna** → Fast code search (functions, classes, patterns)

**Example**: `Task(dipeo-backend, "Add GraphQL timeout field") + Task(dipeo-frontend-dev, "Add timeout UI control")`

See [Agent docs](docs/agents/index.md) for detailed guides.

## Claude Code Skills

DiPeO provides specialized skills for routine code quality and project management tasks. Access skills via the Skill tool.

### Router Skills (Agent Documentation)

Router skills provide on-demand access to agent documentation with 80-90% token reduction vs. automatic injection.

**Available Router Skills:**
- **dipeo-backend**: Backend ecosystem (server/ + cli/): FastAPI server, CLI tools, database, MCP integration
- **dipeo-package-maintainer**: Runtime Python code, handlers, service architecture
- **dipeo-codegen-pipeline**: TypeScript → IR → Python/GraphQL pipeline
- **dipeo-frontend-dev**: React components, visual diagram editor, GraphQL integration, TypeScript types

**How Router Skills Work:**
- **Thin routers** (~50-100 lines): Decision criteria, doc anchors, escalation paths
- **Progressive**: Use `Skill(dipeo-backend)` to load router → check if task is simple
- **doc-lookup**: Load specific sections: `Skill(doc-lookup) --query "cli-commands"`
- **Token efficiency**: 80-90% reduction (1.5k vs 15k tokens per task)

**When to Use:** Before Task tool invocation or during agent execution

See `.claude/skills/` for detailed skill documentation.

### todo-manage Skill

Use for comprehensive TODO management on multi-phase projects (3+ phases or 10+ tasks), complex migrations, or large feature implementations.

**Access**: `/dipeotodos` slash command

**Don't use for**: Simple single-task changes (use TodoWrite tool instead)

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
- **Database**: SQLite at `.dipeo/data/dipeo_state.db` - see [Database Schema](docs/database-schema.md) (auto-generated via `make schema-docs`)

### Key Directories
- `/cli/` - Command-line tools (dipeo, dipeocc commands)
- `/server/` - FastAPI backend (GraphQL API, MCP integration)
- `/apps/web/` - React frontend
- `/dipeo/` - Core Python library (application/domain/infrastructure)
- `/dipeo/models/src/` - TypeScript specs (source of truth)
- `/dipeo/diagram_generated/` - Generated code (don't edit)

See [Overall Architecture](docs/architecture/README.md) for complete details.

## Adding New Features

- **New Node Types**: TypeScript spec → codegen → handlers → update schema. See [Developer Guide](docs/guides/developer-guide-diagrams.md)
- **New Diagram Formats**: Create strategy (parser/transformer/serializer). See [Developer Guide](docs/guides/developer-guide-diagrams.md#adding-new-diagram-formats)
- **GraphQL Operations**: Add definition in `/dipeo/models/src/frontend/query-definitions/` → codegen. See [GraphQL Layer](docs/architecture/graphql-layer.md)
- **API/UI Changes**: Modify schema → `make graphql-schema` or work in `/apps/web/src/`

## Important Notes

- **Python 3.13+** required
- **uv** for Python, **pnpm** for JavaScript (not npm/yarn)
- Default LLM: `gpt-5-nano-2025-08-07`
- Backend: port 8000, Frontend: port 3000
- Debug with `--debug` flag, check `.dipeo/logs/cli.log`
- **Database**: SQLite at `.dipeo/data/dipeo_state.db` with 3 tables (executions, messages, transitions)
  - Schema docs: `docs/database-schema.md` (regenerate with `make schema-docs`)
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
