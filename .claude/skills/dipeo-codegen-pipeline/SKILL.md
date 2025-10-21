---
name: dipeo-codegen-pipeline
description: Router skill for DiPeO code generation pipeline (TypeScript specs → IR → Python/GraphQL). Use when task mentions TypeScript models, IR builders, generated code diagnosis, or codegen workflow. For simple tasks, handle directly; for complex work, escalate to dipeo-codegen-pipeline agent.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

# DiPeO Codegen Pipeline Router

**Domain**: Complete TypeScript → IR → Python/GraphQL pipeline (`/dipeo/models/src/`, `/dipeo/infrastructure/codegen/`, generated code diagnosis).

## Quick Decision: Skill or Agent?

### ✅ Handle Directly (This Skill)
- **Simple lookups**: Understanding codegen workflow, reviewing TypeScript specs
- **Read-only tasks**: Checking generated code structure, reviewing IR output
- **Pattern reference**: snake_case naming rules, type mapping examples
- **Small spec tweaks**: Minor TypeScript field changes (<5 lines, 1 file)
- **Workflow questions**: "How do I run codegen?", "What's the IR structure?"

### ❌ Escalate to Agent
- **New node types**: Creating complete TypeScript specs with IR builders
- **IR builder changes**: Modifying AST processing, type conversion logic
- **Generated code diagnosis**: Tracing why generated code is wrong
- **Template modifications**: Changing Jinja templates for code generation
- **Complex spec changes**: Multi-field changes affecting multiple generated files
- **Type system updates**: Changes to UnifiedTypeConverter or type mappings

**Agent**: `Task(dipeo-codegen-pipeline, "your detailed task description")`

## Documentation Sections (Load On-Demand)

Use `Skill(doc-lookup)` with these anchors when you need detailed context:

**Overview & Ownership**:
- `docs/agents/codegen-pipeline.md#overview` - Pipeline overview and ownership

**TypeScript Model Design**:
- `docs/agents/codegen-pipeline.md#typescript-model-design` - Design principles and file structure
- `docs/agents/codegen-pipeline.md#2-naming-standards` - **CRITICAL**: snake_case rules
- `docs/agents/codegen-pipeline.md#workflow-creating-new-node-types` - New node workflow

**IR Builder System**:
- `docs/agents/codegen-pipeline.md#ir-builder-system` - Architecture and pipeline system
- `docs/agents/codegen-pipeline.md#type-system` - Type conversion and AST processing

**Code Generation**:
- `docs/agents/codegen-pipeline.md#code-generation` - Template system and output structure
- `docs/agents/codegen-pipeline.md#generation-workflow` - Complete make codegen workflow

**Diagnosis**:
- `docs/agents/codegen-pipeline.md#tracing-generation-issues` - Diagnosing generated code
- `docs/agents/codegen-pipeline.md#your-critical-responsibility` - Unique diagnosis role

**Workflows & Collaboration**:
- `docs/agents/codegen-pipeline.md#complete-workflow` - End-to-end workflow steps
- `docs/agents/codegen-pipeline.md#when-to-engage-other-agents` - Escalation guidance

**Example doc-lookup call**:
```bash
python .claude/skills/doc-lookup/scripts/section_search.py \
  --query "naming-standards" \
  --paths docs/agents/codegen-pipeline.md \
  --top 1
```

## Escalation to Other Agents

**To dipeo-package-maintainer**: Runtime handler issues, service architecture (if generated code is correct)
**To dipeo-backend**: GraphQL schema deployment, server config (if generation is correct)

## Typical Workflow

1. **Assess complexity**: Simple lookup/guidance vs. complex generation task
2. **If simple**: Load relevant section via `Skill(doc-lookup)`, provide guidance
3. **If diagnosis needed**: Trace TypeScript → IR → Python (use diagnosis docs)
4. **If complex**: Escalate with `Task(dipeo-codegen-pipeline, "task details")`
