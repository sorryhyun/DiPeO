# DiPeO Project Todos

---

## In Progress

### Agent Documentation Migration: PreToolUse Hook → Skills 🚧
**Started**: 2025-10-19
**Estimated effort**: ~6 hours (7 tasks across 5 phases)

**Goal**: Migrate from automatic documentation injection via PreToolUse hook to on-demand skill-based documentation loading. This reduces context bloat, provides granular control, and enables better separation between documentation (skills) and execution (agents).

**Architectural Context**:

This migration represents a fundamental shift in how DiPeO's specialized agents access documentation:

**Current Architecture (Automatic Injection)**:
- PreToolUse hook intercepts every Task tool invocation
- `inject-agent-docs.py` automatically injects 1500+ lines before agent starts
- **Problem**: Claude Code (orchestrator) decides what docs to load based on agent type
- **Limitation**: All-or-nothing - loads entire doc set even if only small portion needed
- **Cost**: High token usage, context bloat, reduced reasoning space

**New Architecture (Agent-Driven Retrieval)**:
- Skills provide documentation on-demand via `Skill(agent-name)` invocation
- **Key change**: Sub-agents themselves decide when they need documentation
- **Responsibility shift**: From orchestrator (Claude Code) → to sub-agent (specialized agent)
- **Granularity**: Sub-agents can request specific skill subdomains (e.g., `Skill(backend-cli)` vs `Skill(backend-mcp)`)
- **Decision support**: Skills include criteria for when to escalate to full agent invocation

**Why This Matters**:
1. **Autonomy**: Sub-agents gain agency to request context when needed, not receive it automatically
2. **Efficiency**: Only load relevant documentation for the specific task at hand
3. **Composability**: Can layer skills (load backend-cli, then backend-mcp) as investigation deepens
4. **Separation of Concerns**: Skills = knowledge retrieval, Agents = task execution
5. **Scalability**: Easy to add targeted sub-domain skills without polluting agent definitions

**Usage Pattern Shift**:
```
# OLD: Automatic (orchestrator decides)
Task(dipeo-backend, "Fix CLI bug")
→ PreToolUse hook injects ALL backend docs (CLI + MCP + DB + Server)

# NEW: On-demand (agent decides)
Task(dipeo-backend, "Fix CLI bug")
→ Agent thinks: "I need CLI context"
→ Agent invokes: Skill(backend-cli)
→ Gets targeted CLI docs only
→ Completes fix with minimal context
```

This aligns with DiPeO's philosophy of autonomous, intelligent agents that manage their own information needs rather than receiving predetermined context bundles.

**Planned Tasks**:

**Phase 1: Investigation & Planning** ✅
- [x] Analyze current injection system (PreToolUse hook + inject-agent-docs.py)
- [x] Review agent structure (.claude/agents/ + docs/agents/)
- [x] Examine skill structure and patterns
- [x] Design hybrid skill architecture

**Phase 2: Create Main Agent Skills**
- [ ] Create `dipeo-backend` skill
  - Use `Skill(generate-skill)` to scaffold structure
  - Copy content from `docs/agents/backend-development.md`
  - Add "When to Invoke Agent" section with decision criteria
  - Add cross-references to architecture docs and related skills

- [ ] Create `dipeo-package-maintainer` skill
  - Use `Skill(generate-skill)` to scaffold structure
  - Copy content from `docs/agents/package-maintainer.md`
  - Add decision criteria for agent invocation vs. direct handling
  - Add escalation guidance to other agents

- [ ] Create `dipeo-codegen-pipeline` skill
  - Use `Skill(generate-skill)` to scaffold structure
  - Copy content from `docs/agents/codegen-pipeline.md`
  - Add workflow guidance (TypeScript → IR → Python/GraphQL)
  - Add troubleshooting and common patterns

**Phase 3: Update Agent Definitions**
- [ ] Modify `.claude/agents/dipeo-backend.md`
  - Add "For detailed docs: use Skill(dipeo-backend)" to frontmatter description
  - Simplify content to focus on brief scope and examples

- [ ] Modify `.claude/agents/dipeo-package-maintainer.md`
  - Add skill reference to frontmatter description
  - Keep ownership boundaries and examples

- [ ] Modify `.claude/agents/dipeo-codegen-pipeline.md`
  - Add skill reference to frontmatter description
  - Maintain clarity on what agent owns vs. doesn't own

- [ ] Update `scripts/inject-agent-docs.py`
  - Add deprecation notice in header comments
  - Explain migration to skills

**Phase 4: Remove PreToolUse Hook**
- [ ] Remove hook from `.claude/settings.local.json`
  - Delete PreToolUse hook configuration block
  - Verify no other hooks depend on injection script

- [ ] Archive injection script
  - Create `scripts/deprecated/` directory if needed
  - Move `inject-agent-docs.py` to `scripts/deprecated/inject-agent-docs.py`
  - Add README explaining why it was deprecated

**Phase 5: Testing & Validation**
- [ ] Test agent invocation without hook
  - Invoke `Task(dipeo-backend)` and verify it works
  - Invoke `Skill(dipeo-backend)` and verify docs load
  - Test workflow: skill → docs → decide → maybe invoke agent

- [ ] Update documentation
  - Update `CLAUDE.md` to explain skill-based docs
  - Update `docs/agents/index.md` with new workflow
  - Add usage examples to README

**Files to be created**:
- `.claude/skills/dipeo-backend/SKILL.md`
- `.claude/skills/dipeo-package-maintainer/SKILL.md`
- `.claude/skills/dipeo-codegen-pipeline/SKILL.md`
- `scripts/deprecated/` (directory)
- `scripts/deprecated/inject-agent-docs.py` (moved)
- `scripts/deprecated/README.md`

**Files to be modified**:
- `.claude/agents/dipeo-backend.md` - Add skill reference, simplify content
- `.claude/agents/dipeo-package-maintainer.md` - Add skill reference, simplify content
- `.claude/agents/dipeo-codegen-pipeline.md` - Add skill reference, simplify content
- `.claude/settings.local.json` - Remove PreToolUse hook
- `CLAUDE.md` - Add skills section, update agent usage
- `docs/agents/index.md` - Document new skill-based workflow

**Files to be deleted**:
- PreToolUse hook block in `.claude/settings.local.json`

**Benefits to be delivered**:
1. **On-demand loading**: Only load docs when needed, reducing context bloat
2. **Granular control**: Can have multiple skills per domain for targeted documentation
3. **Better separation**: Skills for docs, agents for execution
4. **Flexibility**: Invoke skill for context, then decide whether to use agent
5. **Scalability**: Easy to add granular skills (e.g., `backend-cli`, `backend-mcp`) later
6. **Performance**: Reduced token usage by avoiding automatic injection
7. **Decision support**: Skills include criteria for when to invoke agents

**Usage examples**:
```bash
# Get backend documentation on-demand
Skill(dipeo-backend)

# Review docs, decide simple enough to handle directly
# (make change without invoking agent)

# Or invoke agent if complex
Task(dipeo-backend, "Add new CLI command for metrics export")

# Hybrid workflow: skill for context + agent for execution
Skill(dipeo-codegen-pipeline)  # Load TypeScript → Python pipeline docs
Task(dipeo-codegen-pipeline, "Add new node type for webhooks")
```

**Future enhancements** (optional):
- Add granular skills: `backend-cli`, `backend-mcp`, `backend-db`
- Add granular skills: `codegen-typescript`, `codegen-ir`, `codegen-graphql`
- Cross-reference skills in agent definitions
- Create skill invocation shortcuts in CLAUDE.md

---

_Use `/dipeotodos` to view this file anytime._
