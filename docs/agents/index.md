# Agent Documentation Index

This directory contains detailed development guides for DiPeO's specialized Claude Code subagents. Each guide provides comprehensive context, workflows, and best practices for its respective domain.

## Core Development Agents

### [Core Python Development](core-python-development.md)
**Agent**: `dipeo-core-python`
**Domain**: Backend Python business logic, execution handlers, runtime infrastructure, service architecture
**Key Areas**: `/dipeo/application/`, `/dipeo/domain/`, `/dipeo/infrastructure/` (runtime only, not codegen)
**Role**: Consumes generated code as read-only dependency, implements application logic

### [Frontend Development](frontend-development.md)
**Agent**: `dipeo-frontend-dev`
**Domain**: React components, visual diagram editor (XYFlow), GraphQL integration
**Key Areas**: `/apps/web/src/`, TypeScript/React, GraphQL hooks

### [TypeScript Model Design](typescript-model-design.md)
**Agent**: `typescript-model-designer`
**Domain**: TypeScript specifications - single source of truth for domain models
**Key Areas**: `/dipeo/models/src/` (owns all TypeScript source)
**Role**: Designs specs, coordinates with codegen-specialist for generation validation

### [Code Generation Pipeline](codegen-pipeline.md)
**Agent**: `dipeo-codegen-specialist`
**Domain**: **Bridge agent** - owns entire codegen infrastructure & generated code diagnosis
**Key Areas**: `/dipeo/infrastructure/codegen/` (full ownership), generated code review
**Role**: Validates specs, runs pipeline, diagnoses generated code, coordinates between TS & Python

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
