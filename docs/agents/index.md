# Agent Documentation Index

This directory contains detailed development guides for DiPeO's specialized Claude Code subagents. Each guide provides comprehensive context, workflows, and best practices for its respective domain.

## Core Development Agents

### [Core Python Development](core-python-development.md)
**Agent**: `dipeo-core-python`
**Domain**: Backend Python business logic, execution handlers, infrastructure, service architecture
**Key Areas**: `/dipeo/application/`, `/dipeo/domain/`, `/dipeo/infrastructure/`

### [Frontend Development](frontend-development.md)
**Agent**: `dipeo-frontend-dev`
**Domain**: React components, visual diagram editor (XYFlow), GraphQL integration
**Key Areas**: `/apps/web/src/`, TypeScript/React, GraphQL hooks

### [TypeScript Model Design](typescript-model-design.md)
**Agent**: `typescript-model-designer`
**Domain**: TypeScript specifications that drive code generation
**Key Areas**: `/dipeo/models/src/`, node specs, query definitions

### [Code Generation Pipeline](codegen-pipeline.md)
**Agent**: `dipeo-codegen-specialist`
**Domain**: Code generation system, IR builders, staging validation
**Key Areas**: `/dipeo/infrastructure/codegen/`, TypeScript→Python pipeline

## Feature-Specific Agents

### [DiPeOCC Conversion](dipeocc-conversion.md)
**Agent**: `dipeocc-converter`
**Domain**: Converting Claude Code sessions to DiPeO diagrams
**Key Areas**: Session parsing, diagram generation, workflow replay

### [Documentation Maintenance](documentation-maintenance.md)
**Agent**: `docs-maintainer`
**Domain**: Keeping documentation current after code changes
**Key Areas**: `/docs/`, proactive documentation updates

### [Task Management](task-management.md)
**Agent**: `todo-manager`
**Domain**: Planning, organizing, and tracking tasks in TODO.md
**Key Areas**: Task breakdown, prioritization, progress tracking

## Utility Agents

### [TypeScript Type Checking](typecheck-fixing.md)
**Agent**: `typecheck-fixer`
**Domain**: Resolving TypeScript type errors in frontend code
**Key Areas**: Type safety, error analysis, proper fixes

### [Import Refactoring](import-refactoring.md)
**Agent**: `import-refactor-updater`
**Domain**: Updating imports and references after refactoring
**Key Areas**: Module moves, renames, reference updates

### [Code Auditing](code-auditing.md)
**Agent**: `codebase-auditor`
**Domain**: Targeted code analysis for security, performance, quality
**Key Areas**: Pattern detection, issue identification, audit reports

### [Comment Cleanup](comment-cleanup.md)
**Agent**: `comment-cleaner`
**Domain**: Removing redundant comments while preserving valuable ones
**Key Areas**: Code clarity, documentation quality

### [ChatGPT Integration](chatgpt-integration.md)
**Agent**: `chatgpt-project-manager`
**Domain**: Managing DiPeO project in ChatGPT, web automation
**Key Areas**: Project sync, AI model interaction, research automation

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
- [Overall Architecture](../architecture/overall_architecture.md) - System architecture
- [Code Generation Guide](../projects/code-generation-guide.md) - Codegen workflow
- [CLAUDE.md](../../CLAUDE.md) - Main project guidance for Claude Code
