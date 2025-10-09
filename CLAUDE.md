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
dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=40 --timing
dipeo run [diagram] --input-data '{"key": "value"}' --light --debug
dipeo metrics --latest --breakdown  # Profile latest execution
```

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

## Architecture Quick Reference

### Key Concepts
- **Code Generation**: TypeScript specs → IR → Python
- **Avoid editing** `dipeo/diagram_generated/` directly - modify TypeScript specs instead
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

See [Overall Architecture](docs/architecture/overall_architecture.md) for complete details.

## Adding New Features

### New Node Types
1. Create spec in `/dipeo/models/src/nodes/`
2. Build: `cd dipeo/models && pnpm build`
3. Generate: `make codegen` → `make diff-staged` → `make apply-test`
4. Update schema: `make graphql-schema`

### GraphQL Operations
1. Add definition in `/dipeo/models/src/frontend/query-definitions/`
2. Follow codegen workflow above
3. See [GraphQL Layer](docs/architecture/graphql-layer.md)

### Other Changes
- **API changes**: Modify schema → `make graphql-schema`
- **UI changes**: Work in `/apps/web/src/`

## Important Notes

- **Python 3.13+** required
- **uv** for Python, **pnpm** for JavaScript (not npm/yarn)
- Default LLM: `gpt-5-nano-2025-08-07`
- Backend: port 8000, Frontend: port 3000
- Debug with `--debug` flag, check `.logs/cli.log`
- Formal test suite under development

## Common Issues & Solutions

| Issue | Solution | Documentation |
|-------|----------|-------------|
| Import errors | `make install` (uv auto-manages env) | |
| Generated code sync | Run codegen workflow | |
| TypeScript errors | `make graphql-schema` | |
| Need debugging | Add `--debug`, check `.logs/` | |
| Claude Code sessions | Use `dipeocc convert` | |

## Quick Debug Reference

- **Run diagrams**: `dipeo run [diagram] --light --debug`
- **Monitor UI**: `http://localhost:3000/?monitor=true`
- **GraphQL playground**: `http://localhost:8000/graphql`
- **Logs**: `.logs/cli.log` for detailed output

---

**For comprehensive documentation**, see [Documentation Index](docs/index.md) 
