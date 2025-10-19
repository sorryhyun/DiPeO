---
name: dipeo-package-maintainer
description: Router skill for DiPeO runtime Python code (execution handlers, service architecture, domain models, LLM infrastructure). Use when task mentions node handlers, EventBus, ServiceRegistry, Envelope pattern, or domain logic. For simple tasks, handle directly; for complex work, escalate to dipeo-package-maintainer agent.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

# DiPeO Package Maintainer Router

**Domain**: Runtime Python in `/dipeo/` (application, domain, infrastructure - EXCLUDING codegen and generated code).

## Quick Decision: Skill or Agent?

### ✅ Handle Directly (This Skill)
- **Simple changes**: <20 lines, 1-2 files
- **Read-only tasks**: Understanding patterns, reviewing implementation
- **Pattern lookup**: Envelope usage, service registration examples
- **Small fixes**: Typos, minor refactors, simple handler tweaks

**Token cost**: ~1,500 tokens (router + targeted section)

### ❌ Escalate to Agent
- **New node handlers**: Creating handlers with complex logic
- **Service architecture**: EventBus integration, ServiceRegistry configuration
- **Domain model changes**: Conversation management, memory strategies
- **Multi-file refactoring**: Affects >2 files or cross-layer changes
- **Generated code issues**: If generated APIs don't work, escalate to dipeo-codegen-pipeline first

**Agent**: `Task(dipeo-package-maintainer, "your detailed task description")`

## Documentation Sections (Load On-Demand)

Use `Skill(doc-lookup)` with these anchors when you need detailed context:

**Core Architecture**:
- `docs/agents/package-maintainer.md#overview` - High-level overview
- `docs/agents/package-maintainer.md#domain-of-expertise` - What you own
- `docs/agents/package-maintainer.md#ownership-boundaries` - What you DON'T own

**Code Layers**:
- `docs/agents/package-maintainer.md#application-layer` - Handlers, GraphQL, services
- `docs/agents/package-maintainer.md#domain-layer` - Domain logic, compilation
- `docs/agents/package-maintainer.md#infrastructure-layer` - LLM, state, EventBus

**Implementation Guidance**:
- `docs/agents/package-maintainer.md#new-node-handlers` - Creating handlers
- `docs/agents/package-maintainer.md#service-modifications` - ServiceRegistry usage
- `docs/agents/package-maintainer.md#graphql-resolvers` - GraphQL application layer

**Code Patterns**:
- `docs/agents/package-maintainer.md#envelope-pattern` - Output pattern
- `docs/agents/package-maintainer.md#service-registry-pattern` - DI pattern
- `docs/agents/package-maintainer.md#node-handler-pattern` - Handler structure
- `docs/agents/package-maintainer.md#diagram-access-pattern` - Correct diagram queries

**Reference**:
- `docs/agents/package-maintainer.md#key-import-paths` - Common imports
- `docs/agents/package-maintainer.md#escalation-paths` - When to escalate

**Example doc-lookup call**:
```bash
python .claude/skills/doc-lookup/scripts/section_search.py \
  --query "envelope-pattern" \
  --paths docs/agents/package-maintainer.md \
  --top 1
```

## Escalation to Other Agents

**To dipeo-codegen-pipeline**: Generated code issues, TypeScript specs, new node types, GraphQL schema
**To dipeo-backend**: CLI commands, server config, database schema, MCP server

## Typical Workflow

1. **Assess complexity**: Simple pattern lookup vs. complex implementation
2. **If simple**: Load relevant section via `Skill(doc-lookup)`, provide guidance or make small change
3. **If complex**: Escalate with `Task(dipeo-package-maintainer, "task details")`
4. **Generated code problems**: First check if it's a generation issue → escalate to dipeo-codegen-pipeline

---

**Token savings**: ~90% reduction (1,500 vs. 15,000 tokens) for focused tasks
