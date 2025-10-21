---
name: dipeo-backend
description: Router skill for DiPeO backend (FastAPI server, CLI, database, MCP integration). Use when task mentions CLI commands, server endpoints, database queries, or MCP tools. For simple tasks, handle directly; for complex work, escalate to dipeo-backend agent.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

# DiPeO Backend Router

**Domain**: FastAPI server, CLI (`dipeo run/results/metrics/compile/export`), SQLite schema, MCP server integration in `apps/server/`.

## Quick Decision: Skill or Agent?

### ✅ Handle Directly (This Skill)
- **Simple changes**: <20 lines, 1-2 files
- **Read-only tasks**: Understanding code, reviewing configs, debugging logs
- **Documentation lookup**: CLI help, API signatures, database schema
- **Small config tweaks**: Environment variables, command flags

### ❌ Escalate to Agent
- **Complex features**: Multi-file changes, new CLI commands, database migrations
- **Architecture changes**: New API endpoints, MCP tool implementation
- **Cross-cutting concerns**: Affects CLI + database + execution engine
- **Uncertain scope**: Not sure how many files will change

**Agent**: `Task(dipeo-backend, "your detailed task description")`

## Documentation Sections (Load On-Demand)

Use `Skill(doc-lookup)` with these anchors when you need detailed context:

**CLI System**:
- `docs/agents/backend-development.md#cli-system` - CLI architecture and commands
- `docs/agents/backend-development.md#background-execution` - Background execution

**FastAPI Server**:
- `docs/agents/backend-development.md#fastapi-server` - Server overview and responsibilities

**Database & Persistence**:
- `docs/agents/backend-development.md#database-persistence` - SQLite schema and message store

**MCP Server**:
- `docs/agents/backend-development.md#mcp-server` - MCP architecture and implementation
- `docs/features/mcp-server-integration.md#quick-start` - Setup and usage guide
- `docs/features/mcp-server-integration.md#uploading-diagrams` - Diagram push workflow

**ChatGPT Integration**:
- `docs/features/chatgpt-mcp-integration.md#quick-start` - MCP connection setup
- `docs/features/chatgpt-apps-integration.md#overview` - Widget system and architecture

**Troubleshooting**:
- `docs/agents/backend-development.md#troubleshooting` - Common debugging patterns

**Example doc-lookup call**:
```bash
python .claude/skills/doc-lookup/scripts/section_search.py \
  --query "cli-commands" \
  --paths docs/agents/backend-development.md \
  --top 1
```

## Escalation to Other Agents

**To dipeo-package-maintainer**: Execution handlers, service architecture, domain models, LLM infrastructure
**To dipeo-codegen-pipeline**: GraphQL schema changes, generated type issues, TypeScript specs

## Typical Workflow

1. **Assess task complexity**: Simple (handle) vs. complex (escalate)
2. **If simple**: Load relevant section via `Skill(doc-lookup)`
3. **Execute**: Make changes or provide answer
4. **If complex**: Escalate with `Task(dipeo-backend, "task details")`
