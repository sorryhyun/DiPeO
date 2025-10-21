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

**Token cost**: ~1,500 tokens (router + targeted section)

### ❌ Escalate to Agent
- **Complex features**: Multi-file changes, new CLI commands, database migrations
- **Architecture changes**: New API endpoints, MCP tool implementation
- **Cross-cutting concerns**: Affects CLI + database + execution engine
- **Uncertain scope**: Not sure how many files will change

**Agent**: `Task(dipeo-backend, "your detailed task description")`

## Documentation Sections (Load On-Demand)

Use `Skill(doc-lookup)` with these anchors when you need detailed context:

**CLI System**:
- `docs/agents/backend-development.md#cli-system` - Full CLI architecture
- `docs/agents/backend-development.md#cli-commands` - Command examples
- `docs/agents/backend-development.md#cli-architecture` - Parser/dispatcher/runner breakdown
- `docs/agents/backend-development.md#background-execution` - Background execution

**FastAPI Server**:
- `docs/agents/backend-development.md#fastapi-server` - Server overview
- `docs/agents/backend-development.md#core-responsibilities` - What backend owns

**Database & Persistence**:
- `docs/agents/backend-development.md#database-schema` - SQLite schema
- `docs/agents/backend-development.md#database-persistence` - Full DB section
- `docs/agents/backend-development.md#message-store` - Conversation persistence

**MCP Server**:
- `docs/agents/backend-development.md#mcp-server` - MCP architecture overview
- `docs/agents/backend-development.md#mcp-tools` - Available tools
- `docs/agents/backend-development.md#mcp-resources` - Resource implementations
- `docs/agents/backend-development.md#mcp-architecture` - Implementation details
- `docs/agents/backend-development.md#http-transport` - HTTP endpoint configuration
- `docs/features/mcp-server-integration.md#quick-start` - Usage guide
- `docs/features/mcp-server-integration.md#available-tools` - Tool catalog
- `docs/features/mcp-server-integration.md#uploading-diagrams` - Push diagrams to MCP

**ChatGPT Integration**:
- `docs/features/chatgpt-mcp-integration.md#quick-start` - Connect DiPeO to ChatGPT
- `docs/features/chatgpt-mcp-integration.md#available-mcp-tools` - ChatGPT-accessible tools
- `docs/features/chatgpt-mcp-integration.md#troubleshooting` - Connection & auth issues
- `docs/features/chatgpt-mcp-integration.md#security-best-practices` - Security guidance
- `docs/features/chatgpt-apps-integration.md#overview` - Widget system overview
- `docs/features/chatgpt-apps-integration.md#architecture` - Widget architecture
- `docs/features/chatgpt-apps-integration.md#setup` - Widget setup & build process
- `docs/features/chatgpt-apps-integration.md#using-widgets-in-mcp-tools` - Widget integration

**Troubleshooting**:
- `docs/agents/backend-development.md#troubleshooting` - Common debugging patterns
- `docs/agents/backend-development.md#common-patterns` - Implementation patterns

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

---

**Token savings**: ~90% reduction (1,500 vs. 15,000 tokens) for focused tasks
