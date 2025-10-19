# Agent Documentation Index

This directory contains detailed development guides for DiPeO's specialized Claude Code subagents. Each guide provides comprehensive context, workflows, and best practices for its respective domain.

## Core Development Agents

### [Package Maintainer](package-maintainer.md)
**Agent**: `dipeo-package-maintainer`
**Domain**: Runtime Python code in `/dipeo/` - execution engine, handlers, service architecture
**Key Areas**: `/dipeo/application/`, `/dipeo/domain/`, `/dipeo/infrastructure/` (EXCLUDING codegen)
**Role**: Implements runtime execution logic, consumes generated code as read-only dependency
**Responsibilities**: Node handlers, GraphQL resolvers, EventBus, EnhancedServiceRegistry, LLM infrastructure

### [Backend Development](backend-development.md)
**Agent**: `dipeo-backend`
**Domain**: FastAPI server, CLI, database, and MCP integration in `apps/server/`
**Key Areas**: FastAPI server, CLI commands, SQLite database, MCP server
**Role**: Owns all backend infrastructure - server lifecycle, command-line interface, persistence, MCP protocol
**Responsibilities**: GraphQL endpoint, dipeo run/results/metrics/compile/export commands, database schema, message store

### [Code Generation Pipeline](codegen-pipeline.md)
**Agent**: `dipeo-codegen-pipeline`
**Domain**: Complete TypeScript → IR → Python/GraphQL pipeline
**Key Areas**: `/dipeo/models/src/` (TypeScript specs), `/dipeo/infrastructure/codegen/` (IR builders), `dipeo/diagram_generated/` (generated code)
**Role**: Owns entire codegen flow - design TypeScript models, build IR, generate Python/GraphQL, diagnose generated code
**Responsibilities**: TypeScript model design, IR builder system, code generation, generated code diagnosis, type conversion

### [Frontend Development](frontend-development.md)
**Agent**: `dipeo-frontend-dev`
**Domain**: React components, visual diagram editor (XYFlow), GraphQL integration
**Key Areas**: `/apps/web/src/`, TypeScript/React, GraphQL hooks

## Feature-Specific Agents

### [DiPeOCC Conversion](dipeocc-conversion.md)
**Agent**: `dipeocc-converter`
**Domain**: Converting Claude Code sessions to DiPeO diagrams
**Key Areas**: Session parsing, diagram generation, workflow replay


## Utility Agents

### [Code Auditing](code-auditing.md)
**Agent**: `codebase-auditor`
**Domain**: Targeted code analysis for security, performance, quality
**Key Areas**: Pattern detection, issue identification, audit reports


## Agent Documentation Access Pattern

DiPeO uses a **router skills + progressive disclosure** pattern for agent documentation access, achieving 80-90% token reduction vs. automatic injection.

### Router Skills

Router skills provide thin (~50-100 lines) decision support for each agent domain:

- **Skill(dipeo-backend)**: Backend server, CLI, database, MCP integration
- **Skill(dipeo-package-maintainer)**: Runtime Python, handlers, service architecture
- **Skill(dipeo-codegen-pipeline)**: TypeScript → IR → Python/GraphQL pipeline
- **Skill(dipeo-frontend-dev)**: React components, visual diagram editor, GraphQL integration, TypeScript types

**What Router Skills Provide:**
1. **Decision criteria**: When to handle directly vs. invoke full agent
2. **Stable documentation anchors**: References to specific sections in agent docs
3. **Escalation paths**: Clear guidance on when to use other agents/skills

### Progressive Documentation Loading

Instead of automatic injection, use **doc-lookup skill** to load specific sections:

```bash
# Example: Load specific CLI documentation section
Skill(doc-lookup) --query "cli-commands" --paths docs/agents/backend-development.md
```

### Workflow Patterns

**Pattern 1: Router → Direct Handling (Simple Task)**
```
Skill(dipeo-backend)           # Load router (~50 lines)
→ Review decision criteria
→ Task is simple, handle directly
→ Cost: ~1,000 tokens
```

**Pattern 2: Router → Doc-Lookup → Solve (Focused Task)**
```
Skill(dipeo-backend)                        # Load router
→ Identify need for CLI section
→ Skill(doc-lookup) --query "cli-commands"  # Load ~50 lines
→ Solve with targeted context
→ Cost: ~1,500 tokens (vs. 15,000 with auto-injection)
```

**Pattern 3: Router → Escalate to Agent (Complex Task)**
```
Skill(dipeo-backend)                             # Load router
→ Review decision criteria
→ Task is complex (multi-file, architectural)
→ Task(dipeo-backend, "Add CLI command")         # Invoke full agent
→ Agent loads additional sections via doc-lookup as needed
```

### Benefits

- **Token efficiency**: 80-90% reduction (1.5k vs 15k tokens per task)
- **Progressive disclosure**: Load only relevant sections
- **Agent autonomy**: Agents request context when needed (not automatic)
- **Single source of truth**: Skills reference docs, don't duplicate content
- **No drift**: Stable anchors ensure consistency

### Documentation Anchors

Each agent guide contains stable anchors (heading IDs) for targeted section retrieval:

**backend-development.md anchors:**
- `#cli-implementation` - CLI architecture and commands
- `#mcp-server` - MCP server integration
- `#database-schema` - SQLite schema and persistence

**package-maintainer.md anchors:**
- `#handler-patterns` - Node handler implementation
- `#service-architecture` - EnhancedServiceRegistry, EventBus
- `#graphql-resolvers` - Application layer GraphQL resolvers

**codegen-pipeline.md anchors:**
- `#typescript-specs` - Model design in /dipeo/models/src/
- `#ir-builders` - IR generation infrastructure
- `#generated-code-diagnosis` - Debugging generated code

**frontend-development.md anchors:**
- `#react-components` - React component development patterns
- `#diagram-editor` - Visual diagram editor (XYFlow) guidance
- `#graphql-integration` - GraphQL integration patterns
- `#typescript-types` - TypeScript and type safety practices
- `#component-patterns` - Component best practices
- `#graphql-usage` - GraphQL query/mutation patterns with examples
- `#state-management-general` - General state management guidance
- `#state-management-zustand` - Zustand-specific patterns

See individual agent guides for complete anchor lists.

## How to Use These Guides

Each agent guide contains:
- **Role & Responsibilities**: What the agent does
- **Architecture & Context**: Deep technical background
- **Workflows & Procedures**: Step-by-step guides for common tasks
- **Code Examples**: Practical patterns and conventions
- **Quality Standards**: Pre-completion checklists
- **Troubleshooting**: Common issues and solutions
- **Related Documentation**: Links to other relevant docs

## When to Reference

- **Main agent**: Uses brief routing logic in `.claude/agents/*.md` frontmatter
- **Subagents**: Reference these detailed guides via `docs/agents/[guide].md` syntax
- **Developers**: Read these guides to understand agent capabilities and constraints

## Related Documentation

- [Documentation Index](../index.md) - Complete documentation overview
- [Overall Architecture](../architecture/README.md) - System architecture
- [Code Generation Guide](../projects/code-generation-guide.md) - Codegen workflow
- [CLAUDE.md](../../CLAUDE.md) - Main project guidance for Claude Code
