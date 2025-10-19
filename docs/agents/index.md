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
