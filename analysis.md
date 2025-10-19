# DiPeO Sub-Agent & Skill Architecture Analysis

**Date**: 2025-10-19
**Purpose**: Comprehensive analysis of DiPeO's current sub-agent architecture and migration strategy from automatic documentation injection to on-demand skill-based retrieval

---

## Executive Summary

DiPeO uses specialized Claude Code sub-agents to handle complex domain-specific tasks across a sophisticated monorepo architecture. Currently, these agents receive 50k-80k characters of documentation automatically via a PreToolUse hook before every invocation. This analysis examines why this architecture exists, its current pain points, and proposes a migration to on-demand skill-based documentation retrieval.

**Key Findings**:
- **Current overhead**: 1,400-2,300 lines injected per agent invocation (all-or-nothing)
- **Agent count**: 8 specialized agents with clear domain boundaries
- **Documentation size**: ~2,000 total lines across agent guides
- **Proposed solution**: Migrate to skills for on-demand, granular documentation loading

---

## Table of Contents

1. [What DiPeO Aims to Accomplish](#1-what-dipeo-aims-to-accomplish)
2. [Current Sub-Agent Architecture](#2-current-sub-agent-architecture)
3. [Why These Agents Exist](#3-why-these-agents-exist)
4. [Current Documentation Injection System](#4-current-documentation-injection-system)
5. [Pain Points & Problems](#5-pain-points--problems)
6. [Skills vs. Agents: Architectural Distinction](#6-skills-vs-agents-architectural-distinction)
7. [Migration Strategy](#7-migration-strategy)
8. [Implementation Details](#8-implementation-details)
9. [Future Enhancements](#9-future-enhancements)
10. [Risks & Mitigation](#10-risks--mitigation)

---

## 1. What DiPeO Aims to Accomplish

### Core Mission

DiPeO (Diagrammed People & Organizations) is an **open-source platform for visual AI workflow programming**. It enables developers to design, execute, and monitor multi-agent AI workflows through visual diagrams instead of writing imperative code.

### System Architecture

DiPeO is a sophisticated monorepo with three main layers:

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (apps/web/)                                   │
│  React 19 + XYFlow visual diagram editor                │
│  GraphQL client consuming generated hooks               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Backend (apps/server/)                                 │
│  FastAPI + Strawberry GraphQL server                    │
│  CLI (dipeo run, results, metrics, compile, export)     │
│  Database (SQLite): executions, messages, transitions   │
│  MCP Server: Expose diagrams as tools via MCP protocol  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Core Package (dipeo/)                                  │
│  Execution engine + handlers                            │
│  Service architecture (EventBus, ServiceRegistry)       │
│  Domain models (execution, conversation, diagram)       │
│  LLM infrastructure (5+ providers)                      │
└─────────────────────────────────────────────────────────┘
```

### Key Technical Characteristics

1. **Code Generation Pipeline**: TypeScript model specs → IR builders → Python/GraphQL code generation
2. **Generated Code**: `dipeo/diagram_generated/` contains 5,000+ lines of auto-generated code (READ-ONLY)
3. **Configuration-Driven**: HandleSpec tables, field mappings - no if-elif chains
4. **Service Architecture**: EnhancedServiceRegistry, EventBus, mixin-based composition
5. **Multi-Format Diagrams**: Light YAML, Readable format support via strategy pattern

### Development Complexity

- **Languages**: Python 3.13, TypeScript, React 19
- **Package managers**: uv (Python), pnpm (JavaScript)
- **Lines of code**: ~50k+ across all layers
- **Documentation**: ~8,000 lines of technical docs
- **Domain boundaries**: 8 distinct domains requiring specialized expertise

**Why this matters**: The codebase complexity and clear domain boundaries necessitate specialized sub-agents with deep contextual knowledge.

---

## 2. Current Sub-Agent Architecture

### Agent Inventory

DiPeO employs 8 specialized sub-agents, categorized by purpose:

#### Core Development Agents (3)

| Agent | Domain | Files Owned | Responsibilities |
|-------|--------|-------------|------------------|
| **dipeo-backend** | Backend server, CLI, DB, MCP | `apps/server/` | FastAPI server, CLI commands (run/results/metrics/compile/export), SQLite schema, MCP server, message store |
| **dipeo-package-maintainer** | Core Python runtime | `/dipeo/application/`, `/dipeo/domain/`, `/dipeo/infrastructure/` (EXCLUDING codegen) | Execution handlers, GraphQL resolvers, service architecture, EventBus, EnhancedServiceRegistry, LLM providers |
| **dipeo-codegen-pipeline** | Code generation | `/dipeo/models/src/` (TypeScript specs), `/dipeo/infrastructure/codegen/` (IR builders), `dipeo/diagram_generated/` (diagnosis) | TypeScript model design, IR builder system, code generation, generated code diagnosis |

#### Feature-Specific Agents (2)

| Agent | Domain | Responsibilities |
|-------|--------|------------------|
| **dipeo-frontend-dev** | React frontend | React components, XYFlow editor, GraphQL integration, TypeScript type fixing |
| **dipeocc-converter** | Claude Code integration | Convert Claude Code sessions to DiPeO diagrams, workflow replay |

#### Utility Agents (3)

| Agent | Purpose |
|-------|---------|
| **codebase-auditor** | Targeted code analysis (security, performance, quality) |
| **code-polisher** | Routine cleanup (comment removal, import updates, file separation) |
| **codebase-qna** | Fast code retrieval using Haiku (delegated search tasks) |

### Agent File Structure

Each agent has two files:

1. **Agent Definition** (`.claude/agents/{name}.md`):
   - Frontmatter: name, description, model, color
   - Brief scope summary (50-100 lines)
   - Routing examples
   - Quick reference

2. **Agent Documentation** (`docs/agents/{name}.md`):
   - Comprehensive guide (200-800 lines)
   - Architecture context
   - Workflows and procedures
   - Code examples and patterns
   - Quality standards
   - Troubleshooting

**Current injection mechanism**: The PreToolUse hook automatically injects the comprehensive documentation into every agent invocation.

---

## 3. Why These Agents Exist

### Problem: Cognitive Complexity Management

DiPeO's architecture spans multiple technical domains that require different expertise:

1. **Backend Engineering**: FastAPI, SQLite, GraphQL, MCP protocol
2. **Core Python Architecture**: Service patterns, execution engine, event-driven design
3. **Code Generation**: TypeScript AST parsing, IR transformation, template generation
4. **Frontend Development**: React 19, XYFlow, GraphQL client integration
5. **Specialized Workflows**: Session conversion, code auditing, quality maintenance

**Without specialized agents**, a single Claude Code session would need to:
- Hold 50k+ LOC across 3 languages in context
- Understand 5+ distinct architectural patterns
- Navigate generated vs. hand-written code boundaries
- Make routing decisions without domain expertise

### Solution: Domain-Driven Agent Decomposition

Each agent embodies **deep expertise in a specific subdomain**:

#### dipeo-backend: Infrastructure Ownership
- **Why it exists**: Backend concerns (server, CLI, database) are orthogonal to execution logic
- **What it prevents**: Core package maintainer editing backend code, backend developers modifying execution handlers
- **Key principle**: "You own apps/server/, you do NOT own /dipeo/"

#### dipeo-package-maintainer: Runtime Execution
- **Why it exists**: Execution logic requires understanding of service architecture, EventBus, generated code consumption
- **What it prevents**: Backend developers modifying handlers, codegen specialists implementing runtime logic
- **Key principle**: "You consume generated code as READ-ONLY, you implement handlers"

#### dipeo-codegen-pipeline: Source of Truth Management
- **Why it exists**: Code generation requires understanding TypeScript → IR → Python transformation
- **What it prevents**: Runtime developers editing generated code, confusion about where to make changes
- **Key principle**: "You own the pipeline. If generated code is wrong, you diagnose the generation, not the output"

### Clear Escalation Boundaries

Each agent knows **when to escalate** to another agent:

```
User: "The person_job handler is failing"
├─ dipeo-backend: ❌ "Not my domain" → Escalate to package-maintainer
├─ dipeo-package-maintainer: ✅ "I own handlers" → Handle directly
└─ dipeo-codegen-pipeline: ❌ "Runtime issue" → Escalate to package-maintainer

User: "The generated operations.py looks wrong"
├─ dipeo-backend: ❌ "Not my domain" → Escalate to codegen-pipeline
├─ dipeo-package-maintainer: ❌ "Generated code diagnosis" → Escalate to codegen-pipeline
└─ dipeo-codegen-pipeline: ✅ "I diagnose generated code" → Handle directly
```

**Why escalation matters**: Prevents agents from working outside their expertise, reduces context waste, ensures correct agent handles each task.

---

## 4. Current Documentation Injection System

### Architecture: PreToolUse Hook

**Location**: `.claude/settings.local.json` lines 72-83

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Task",
      "hooks": [
        {
          "type": "command",
          "command": "python3 scripts/inject-agent-docs.py"
        }
      ]
    }
  ]
}
```

### Injection Script: `scripts/inject-agent-docs.py`

**Mechanism**:
1. Hook intercepts every `Task` tool invocation
2. Extracts `subagent_type` parameter from tool input
3. Looks up documentation files in `AGENT_DOCS_MAP`
4. Reads and concatenates all mapped files
5. Wraps in `<agent_documentation>` tags
6. Injects into agent's prompt BEFORE agent starts

### Documentation Mapping

```python
AGENT_DOCS_MAP = {
    "dipeo-package-maintainer": [
        "docs/agents/package-maintainer.md",           # 800+ lines
        "docs/architecture/README.md",                 # 400+ lines
        "docs/architecture/detailed/graphql-layer.md", # 200+ lines
    ],
    "dipeo-backend": [
        "docs/agents/backend-development.md",          # 600+ lines
        "docs/architecture/README.md",                 # 400+ lines
        "docs/features/mcp-server-integration.md",     # 300+ lines
        "docs/database-schema.md",                     # 200+ lines
    ],
    "dipeo-codegen-pipeline": [
        "docs/agents/codegen-pipeline.md",             # 1000+ lines
        "docs/projects/code-generation-guide.md",      # 500+ lines
        "docs/architecture/README.md",                 # 400+ lines
        "docs/architecture/detailed/graphql-layer.md", # 200+ lines
    ],
}
```

### Measured Injection Sizes

| Agent | Lines Injected | Character Count | Token Estimate* |
|-------|----------------|-----------------|-----------------|
| dipeo-backend | 2,064 | 61,973 | ~15,500 tokens |
| dipeo-package-maintainer | 1,380 | 50,992 | ~12,750 tokens |
| dipeo-codegen-pipeline | 2,317 | 79,299 | ~19,800 tokens |

*Assuming ~4 chars/token average

### Current Workflow

```
User: "Fix the CLI bug in dipeo run"
    ↓
Claude Code: Task(dipeo-backend, "Fix the CLI bug in dipeo run")
    ↓
PreToolUse Hook: Intercepts Task invocation
    ↓
inject-agent-docs.py:
  - Reads docs/agents/backend-development.md (600 lines)
  - Reads docs/architecture/README.md (400 lines)
  - Reads docs/features/mcp-server-integration.md (300 lines)
  - Reads docs/database-schema.md (200 lines)
  - Total: 2,064 lines injected
    ↓
dipeo-backend agent receives:
  <agent_instruction>
  Fix the CLI bug in dipeo run
  </agent_instruction>
  <agent_documentation>
  [2,064 lines of documentation]
  </agent_documentation>
    ↓
Agent starts with full context (whether needed or not)
```

---

## 5. Pain Points & Problems

### 5.1 All-or-Nothing Context Loading

**Problem**: Every agent invocation loads ALL mapped documentation, regardless of task scope.

**Example**:
```
User: "Update the CLI help text for dipeo run --background"
    ↓
dipeo-backend receives:
  - Full backend development guide (600 lines)
  - Complete architecture overview (400 lines)
  - Entire MCP integration guide (300 lines)
  - Full database schema docs (200 lines)
    ↓
Needed: CLI help text location (~20 lines)
Wasted: 1,500+ lines of irrelevant context
```

**Cost**:
- 15k-20k tokens consumed upfront
- Reduced reasoning space in 200k token budget
- Slower agent startup

### 5.2 Orchestrator Makes Retrieval Decisions

**Problem**: Claude Code (orchestrator) decides what documentation to load based on agent type, not the agent itself.

**Why this is problematic**:
- Orchestrator doesn't know task specifics yet
- Can't make granular decisions (e.g., "load CLI docs only")
- Agent has no agency to request specific context

**Example of missed opportunity**:
```
User: "Fix the MCP server tool registration"
    ↓
Claude Code: Task(dipeo-backend) → Loads ALL backend docs
    ↓
Better approach:
  dipeo-backend agent starts
  → Realizes this is MCP-specific
  → Skill(backend-mcp) to load ONLY MCP docs
  → Solves problem with 1/4 the context
```

### 5.3 No Granularity

**Problem**: Cannot load subdomain-specific documentation.

**Current limitations**:
- Can't load "backend-cli" without also loading "backend-mcp", "backend-db"
- Can't load "codegen-typescript" without also loading "codegen-ir", "codegen-graphql"
- Can't layer documentation as investigation deepens

**Desired workflow**:
```
Task: "Add --format json to dipeo run"
    ↓
dipeo-backend: "I need CLI context"
  → Skill(backend-cli) # Load ONLY CLI docs (200 lines)
  → Solve problem
    ↓
Task: "Also persist format choice to database"
    ↓
dipeo-backend: "Now I need DB context"
  → Skill(backend-db) # Load ONLY database docs (200 lines)
  → Extend solution
```

**Total context**: 400 lines vs. 2,000+ with current system

### 5.4 High Token Usage

**Problem**: Every agent invocation consumes 12k-20k tokens upfront.

**Impact**:
- Reduces available reasoning budget
- Slower for simple tasks that don't need full context
- Inefficient for multi-agent workflows

**Example multi-agent workflow**:
```
Task: "Add webhook node type"
    ↓
dipeo-codegen-pipeline (loads 20k tokens)
  → Designs TypeScript spec
  → Runs codegen
    ↓
dipeo-package-maintainer (loads 13k tokens)
  → Implements webhook handler
  → Tests execution
    ↓
Total overhead: 33k tokens
Potential with skills: ~5k tokens (load only node spec guide + handler pattern guide)
```

### 5.5 Tight Coupling

**Problem**: PreToolUse hook is tightly coupled to agent infrastructure.

**Maintenance issues**:
- Hook must be maintained separately from agents
- Mapping must be updated when docs change
- No versioning between agent definition and injected docs
- Hook runs even for agents that don't need docs (codebase-qna, code-polisher)

### 5.6 No Decision Support

**Problem**: Documentation is reference material, not decision support.

**What's missing**:
- "When should I invoke this agent vs. handle directly?"
- "When should I escalate to another agent?"
- "Is this task complex enough to warrant an agent?"

**Current workaround**: This logic lives in agent examples, not as structured decision criteria.

---

## 6. Skills vs. Agents: Architectural Distinction

### Conceptual Model

| Aspect | Skills | Agents |
|--------|--------|--------|
| **Purpose** | Provide knowledge/documentation | Execute complex tasks |
| **Invocation** | `Skill(name)` | `Task(type, prompt)` |
| **Output** | Documentation expanded in context | Completed work + report |
| **Model** | Uses calling agent's model | Can specify different model |
| **Autonomy** | Passive (provide info) | Active (perform work) |
| **Lifespan** | Single message expansion | Multi-step autonomous execution |

### Skill Characteristics

**What skills provide**:
- Detailed procedural guidance
- Domain knowledge and context
- Decision frameworks ("when to do X")
- Code examples and patterns
- Troubleshooting guides

**What skills do NOT provide**:
- Autonomous task execution
- File modifications
- Multi-step workflows
- Direct interaction with codebase

**Existing skill examples**:
- `todo-manage`: Guidance on creating comprehensive TODO lists
- `clean-comments`: Principles for removing redundant comments
- `import-refactor`: Procedure for updating imports after file moves
- `maintain-docs`: How to keep documentation current
- `separate-monolithic-python`: Strategy for breaking large files

### Agent Characteristics

**What agents provide**:
- Autonomous execution of complex tasks
- Multi-step workflows (read → analyze → modify → test)
- Domain-specific expertise applied to work
- Direct codebase modifications
- Escalation to other agents

**When to use agents**:
- Task requires 5+ steps
- Domain expertise needed (backend, codegen, frontend)
- Multiple files to modify
- Complex decision-making required
- Investigation + implementation combined

### Hybrid Workflow: Skills → Agents

**Proposed pattern**:
```
User: "I need to add a new CLI command for exporting metrics"
    ↓
Claude Code: "This is a backend CLI task"
  → Skill(dipeo-backend) # Load documentation
  → Reviews docs
  → Determines: "This is complex enough to need the agent"
  → Task(dipeo-backend, "Add metrics export command")
    ↓
dipeo-backend agent:
  → Starts without automatic injection
  → Thinks: "I need CLI-specific context"
  → Skill(backend-cli) # Could be a future sub-skill
  → Implements command
  → Returns result
```

**Benefits**:
- Orchestrator can review docs before deciding to invoke agent
- Agent can request specific subdomain context on-demand
- Clear separation: skills provide knowledge, agents apply it

---

## 7. Migration Strategy

### Phase-by-Phase Approach

#### Phase 1: Create Main Agent Skills (3-4 hours)

**Goal**: Create 1:1 skill equivalents of existing agent documentation.

**Tasks**:
1. Create `dipeo-backend` skill
   - Use `Skill(generate-skill)` for structure
   - Copy content from `docs/agents/backend-development.md`
   - Add "When to Invoke Full Agent" section
   - Add decision criteria (simple task vs. complex task)

2. Create `dipeo-package-maintainer` skill
   - Copy from `docs/agents/package-maintainer.md`
   - Add escalation guidance (when to use backend vs. codegen-pipeline)
   - Include handler patterns and service architecture

3. Create `dipeo-codegen-pipeline` skill
   - Copy from `docs/agents/codegen-pipeline.md`
   - Add codegen workflow steps
   - Include TypeScript spec design patterns
   - Add troubleshooting section

**Deliverables**:
- `.claude/skills/dipeo-backend/SKILL.md`
- `.claude/skills/dipeo-package-maintainer/SKILL.md`
- `.claude/skills/dipeo-codegen-pipeline/SKILL.md`

#### Phase 2: Update Agent Definitions (1-2 hours)

**Goal**: Simplify agent definitions and reference skills for detailed docs.

**Tasks**:
1. Modify `.claude/agents/dipeo-backend.md`
   - Add to description: "For detailed docs: use Skill(dipeo-backend)"
   - Simplify content to focus on scope and routing examples
   - Remove duplicated architecture context

2. Modify `.claude/agents/dipeo-package-maintainer.md`
   - Add skill reference to frontmatter
   - Keep ownership boundaries clear
   - Simplify examples

3. Modify `.claude/agents/dipeo-codegen-pipeline.md`
   - Add skill reference
   - Maintain "what you own vs. don't own" clarity
   - Keep escalation patterns

4. Update `scripts/inject-agent-docs.py`
   - Add deprecation notice in header
   - Explain migration to skills
   - Keep functional during transition

**Deliverables**:
- Updated agent definitions (simplified)
- Deprecation notice in injection script

#### Phase 3: Remove PreToolUse Hook (30 minutes)

**Goal**: Disable automatic injection, rely on on-demand skills.

**Tasks**:
1. Remove hook from `.claude/settings.local.json`
   - Delete lines 72-83 (PreToolUse block)
   - Verify no other hooks depend on it

2. Archive injection script
   - Create `scripts/deprecated/` directory
   - Move `inject-agent-docs.py` to `scripts/deprecated/`
   - Add `README.md` explaining deprecation and migration path

**Deliverables**:
- Updated settings (hook removed)
- Archived injection script with explanation

#### Phase 4: Testing & Validation (2-3 hours)

**Goal**: Verify agents work without automatic injection and skills load correctly.

**Tasks**:
1. Test agent invocation without hook
   - Invoke `Task(dipeo-backend, "test task")`
   - Verify agent starts successfully
   - Verify no automatic documentation injection

2. Test skill invocation
   - Invoke `Skill(dipeo-backend)`
   - Verify documentation loads
   - Verify content is complete and accurate

3. Test hybrid workflow
   - Load skill first: `Skill(dipeo-backend)`
   - Review documentation
   - Decide to invoke agent: `Task(dipeo-backend, "complex task")`
   - Verify workflow completes successfully

4. Test on-demand loading within agent
   - Agent invoked without prior skill load
   - Agent decides it needs context
   - Agent invokes `Skill(dipeo-backend)` internally
   - Verify skill content appears in agent's context

**Deliverables**:
- Test results documenting successful workflows
- Any bugs discovered and fixed

#### Phase 5: Documentation Updates (1-2 hours)

**Goal**: Update project documentation to explain new workflow.

**Tasks**:
1. Update `CLAUDE.md`
   - Add "Claude Code Skills" section
   - Explain skill vs. agent distinction
   - Add usage examples
   - Document migration from PreToolUse hook

2. Update `docs/agents/index.md`
   - Add section on skill-based documentation
   - Update workflow diagrams
   - Add "How to Use Skills" section

3. Add migration guide
   - Document the change for future reference
   - Explain why the migration happened
   - Provide before/after examples

**Deliverables**:
- Updated CLAUDE.md
- Updated docs/agents/index.md
- Migration guide (optional)

### Migration Timeline

| Phase | Duration | Can Run in Parallel |
|-------|----------|---------------------|
| Phase 1: Create Skills | 3-4 hours | No (sequential) |
| Phase 2: Update Agents | 1-2 hours | After Phase 1 |
| Phase 3: Remove Hook | 30 min | After Phase 2 |
| Phase 4: Testing | 2-3 hours | After Phase 3 |
| Phase 5: Documentation | 1-2 hours | Parallel with Phase 4 |

**Total estimated effort**: 8-12 hours

---

## 8. Implementation Details

### Skill File Structure

Each skill follows this structure (based on `todo-manage` and `clean-comments` examples):

```markdown
---
name: dipeo-backend
description: Comprehensive guide to DiPeO's backend server, CLI, database, and MCP integration. Use when working in apps/server/ or need context on FastAPI, GraphQL endpoints, CLI commands, database schema, or MCP server implementation.
---

# Backend Development Guide

[High-level overview]

## Core Responsibilities

[Detailed breakdown]

## Architecture Context

[System architecture relevant to this domain]

## Workflows & Procedures

[Step-by-step guides for common tasks]

## Code Examples

[Practical patterns from codebase]

## Decision Criteria: When to Invoke Full Agent

**Use Skill Only (Direct Handling)**:
- Simple configuration changes
- Adding CLI help text
- Minor database query updates
- Reading logs or status

**Invoke Full Agent**:
- Adding new CLI commands
- Implementing MCP tools
- Database schema migrations
- Multi-file server changes

## Escalation Paths

**To dipeo-package-maintainer**:
- Execution handler issues
- Service architecture questions

**To dipeo-codegen-pipeline**:
- GraphQL schema changes needed
- Generated type issues

## Troubleshooting

[Common issues and solutions]

## Quality Checklist

[Pre-completion checks]
```

### Skill Invocation Patterns

#### Pattern 1: Orchestrator Loads Skill, Then Decides

```
User: "Add background execution support to CLI"
    ↓
Claude Code: "Let me learn about the backend first"
  → Skill(dipeo-backend)
  → Reads documentation
  → Thinks: "This requires adding --background flag, modifying dispatcher, updating async handling"
  → Decision: "This is complex (4+ files, async logic), invoke agent"
  → Task(dipeo-backend, "Add background execution support to CLI")
```

#### Pattern 2: Agent Loads Skill On-Demand

```
User: "Fix the MCP tool registration bug"
    ↓
Claude Code: Task(dipeo-backend, "Fix MCP tool registration bug")
    ↓
dipeo-backend agent:
  → Starts without docs
  → Thinks: "I need MCP-specific context"
  → Skill(dipeo-backend) # Load backend docs
  → Locates MCP section in docs
  → Fixes bug
```

#### Pattern 3: Layered Skill Loading (Future Enhancement)

```
User: "Add webhook node type"
    ↓
Claude Code: Task(dipeo-codegen-pipeline, "Add webhook node")
    ↓
dipeo-codegen-pipeline agent:
  → Skill(codegen-typescript) # Load only TypeScript spec design guide
  → Designs spec
  → Skill(codegen-ir) # Load IR builder guide
  → Implements IR builder
  → Skill(codegen-generation) # Load generation guide
  → Generates code
```

### Updated Agent Definition Format

**Before** (`.claude/agents/dipeo-backend.md`):
```markdown
---
name: dipeo-backend
description: [Long description with examples]
model: sonnet
color: blue
---

[80 lines of scope, responsibilities, examples]
```

**After**:
```markdown
---
name: dipeo-backend
description: Backend server, CLI, database, and MCP integration in apps/server/. For detailed documentation: use Skill(dipeo-backend).

Examples:
- <example>User: "The dipeo run command isn't working"
  Assistant: "I'll use the dipeo-backend agent to debug the CLI"
  </example>
model: sonnet
color: blue
---

# Quick Reference
- **FastAPI Server**: apps/server/main.py
- **CLI**: apps/server/cli/
- **Database**: apps/server/infra/
- **MCP**: apps/server/api/mcp_sdk_server/

## Scope
YOU OWN: Server, CLI, database, MCP
YOU DON'T OWN: Execution handlers, codegen, frontend

## For Detailed Documentation
Use `Skill(dipeo-backend)` to load comprehensive guide.
```

**Reduction**: 80 lines → 25 lines (70% reduction in agent definition size)

---

## 9. Future Enhancements

### 9.1 Granular Sub-Skills

Create targeted skills for specific subdomains:

#### Backend Sub-Skills
- `backend-cli`: CLI command implementation only
- `backend-mcp`: MCP server integration only
- `backend-db`: Database schema and queries only
- `backend-server`: FastAPI server configuration only

#### Codegen Sub-Skills
- `codegen-typescript`: TypeScript model design patterns
- `codegen-ir`: IR builder implementation
- `codegen-python`: Python code generation
- `codegen-graphql`: GraphQL schema generation

#### Package Maintainer Sub-Skills
- `package-handlers`: Node handler implementation patterns
- `package-services`: Service architecture (EventBus, ServiceRegistry)
- `package-llm`: LLM infrastructure and providers

**Usage example**:
```
User: "Add --json flag to dipeo run"
    ↓
dipeo-backend: Skill(backend-cli) # Only CLI docs (200 lines)
  → Implements flag
  → Success with 1/10th the context
```

### 9.2 Cross-Reference Network

Add explicit cross-references in skills:

```markdown
## Related Skills
- **For execution logic**: See `Skill(dipeo-package-maintainer)`
- **For GraphQL changes**: See `Skill(dipeo-codegen-pipeline)`
- **For MCP details**: See `Skill(backend-mcp)` (future)

## Related Agents
- **Complex server changes**: Use `Task(dipeo-backend)`
- **Execution handler issues**: Escalate to `Task(dipeo-package-maintainer)`
```

**Benefit**: Skills guide users to related context and appropriate escalation paths.

### 9.3 Skill Composition

Allow skills to reference other skills:

```markdown
# Skill: backend-cli

## Prerequisites
Before using this skill, review:
- `Skill(dipeo-backend)` for overall backend architecture
- `docs/architecture/README.md` for system context

## Deep Dive
For database integration in CLI commands:
- See `Skill(backend-db)` for database patterns
```

### 9.4 Version Tracking

Add version metadata to skills:

```markdown
---
name: dipeo-backend
version: 1.0.0
last_updated: 2025-10-19
codebase_snapshot: commit abc1234
---
```

**Benefit**: Track when skills become stale relative to codebase changes.

### 9.5 Automated Skill Updates

Script to detect when agent documentation changes:

```bash
# scripts/sync-agent-skills.py
# Detects when docs/agents/*.md changes
# Prompts to update corresponding skill
# Ensures skills stay in sync with documentation
```

---

## 10. Risks & Mitigation

### Risk 1: Agents Don't Load Skills When Needed

**Risk**: Agent starts task without loading skill, lacks context, produces poor results.

**Likelihood**: Medium
**Impact**: High (wasted agent invocation)

**Mitigation**:
1. Add "For detailed docs, use Skill(name)" to agent frontmatter description
2. Include skill invocation in agent examples
3. Test with tasks requiring documentation
4. Monitor initial rollout for missed skill loads

**Fallback**: Re-enable PreToolUse hook temporarily if needed

### Risk 2: Skill Content Drifts from Documentation

**Risk**: `docs/agents/*.md` updates but skills not updated, causing inconsistency.

**Likelihood**: Medium
**Impact**: Medium (outdated guidance)

**Mitigation**:
1. Keep skills as thin wrappers pointing to `docs/agents/*.md`
2. Use `include` pattern if possible (skill references doc path)
3. Add reminder to `docs/agents/index.md`: "When updating agent docs, also update skills"
4. Consider automated sync script (future)

**Alternative approach**: Skills could directly reference markdown files instead of copying content:
```markdown
# Skill: dipeo-backend

For comprehensive backend guide, see:
- [Backend Development](../../docs/agents/backend-development.md)
- [MCP Integration](../../docs/features/mcp-server-integration.md)

[Brief summary here]
```

### Risk 3: Skill Proliferation

**Risk**: Too many granular skills become hard to discover and maintain.

**Likelihood**: Low (starts with 3 main skills)
**Impact**: Medium (maintenance burden)

**Mitigation**:
1. Start with 3 main agent skills only
2. Add sub-skills only when clear benefit demonstrated
3. Limit to 10-15 total skills maximum
4. Maintain skill index in `CLAUDE.md`

### Risk 4: Confusion About When to Use Skills vs. Agents

**Risk**: Users don't understand skill vs. agent distinction.

**Likelihood**: Medium
**Impact**: Low (can clarify via examples)

**Mitigation**:
1. Add clear "Skills vs. Agents" section to `CLAUDE.md`
2. Include decision flowchart
3. Provide usage examples for both patterns
4. Add to agent descriptions: "Use Skill(name) for documentation"

**Decision flowchart**:
```
Need information/guidance? → Use Skill
Need work performed? → Use Task (agent)
Unsure if task is complex? → Load Skill first, then decide
```

### Risk 5: Token Usage Not Reduced in Practice

**Risk**: Agents load skills unnecessarily, negating token savings.

**Likelihood**: Low
**Impact**: Medium (no benefit from migration)

**Mitigation**:
1. Monitor token usage before/after migration
2. Track: avg tokens per agent invocation
3. Measure: % of agent invocations that load skill
4. Optimize: if >80% load skill, consider if agent definition needs more context

**Metrics to track**:
- Before migration: Avg 15k tokens/agent invocation (automatic)
- After migration: Target <8k tokens/agent invocation (on-demand)
- Success criteria: 40%+ reduction in average token usage

### Risk 6: Breaking Existing Workflows

**Risk**: Removing PreToolUse hook breaks existing user scripts or workflows.

**Likelihood**: Low (internal tool)
**Impact**: Medium (temporary disruption)

**Mitigation**:
1. Check for any automation relying on hook (unlikely)
2. Keep injection script in `scripts/deprecated/` for reference
3. Document migration in commit message
4. Test all agent invocations before finalizing migration

---

## Conclusion

### Summary of Recommendations

1. **Migrate from PreToolUse hook to skills** for on-demand documentation loading
2. **Create 3 main agent skills** (backend, package-maintainer, codegen-pipeline) as Phase 1
3. **Simplify agent definitions** to focus on routing and scope
4. **Add decision criteria** to skills ("when to invoke full agent")
5. **Test thoroughly** before removing hook entirely
6. **Monitor token usage** to validate 40%+ reduction
7. **Consider granular sub-skills** as Phase 2 (future enhancement)

### Expected Benefits

- **Token reduction**: 40-60% reduction in average tokens per agent invocation
- **Granular control**: Load only relevant subdomain documentation
- **Agent autonomy**: Agents decide when they need context
- **Better separation**: Skills = knowledge, Agents = execution
- **Scalability**: Easy to add targeted sub-skills without polluting agent definitions
- **Flexibility**: Orchestrator can load skill to decide whether to invoke agent

### Why This Aligns with DiPeO's Philosophy

DiPeO's core mission is **autonomous, intelligent workflow execution**. The migration to on-demand skills embodies this principle:

- **Autonomy**: Agents gain agency to request context when needed
- **Intelligence**: Decisions about documentation loading happen at the point of need
- **Efficiency**: Load only what's required for the specific task
- **Composability**: Skills can be layered as investigation deepens

This architectural shift moves from **"receive predetermined context"** to **"request specific context when needed"** - a fundamental improvement in how specialized agents operate.

---

## Appendix: File Inventory

### Files to Create (3)
- `.claude/skills/dipeo-backend/SKILL.md` (600 lines)
- `.claude/skills/dipeo-package-maintainer/SKILL.md` (800 lines)
- `.claude/skills/dipeo-codegen-pipeline/SKILL.md` (1000 lines)

### Files to Modify (6)
- `.claude/agents/dipeo-backend.md` (reduce from 80 to ~25 lines)
- `.claude/agents/dipeo-package-maintainer.md` (reduce from 70 to ~25 lines)
- `.claude/agents/dipeo-codegen-pipeline.md` (reduce from 80 to ~25 lines)
- `.claude/settings.local.json` (remove lines 72-83)
- `CLAUDE.md` (add "Skills" section)
- `docs/agents/index.md` (add skill documentation)

### Files to Archive (1)
- `scripts/deprecated/inject-agent-docs.py` (moved from `scripts/`)
- `scripts/deprecated/README.md` (new, explains deprecation)

### Total Work Estimate
- **Lines to write**: ~2,400 (3 skills)
- **Lines to modify**: ~200 (agent definitions + docs)
- **Lines to delete**: ~100 (hook configuration)
- **Total effort**: 8-12 hours

---

**End of Analysis**
