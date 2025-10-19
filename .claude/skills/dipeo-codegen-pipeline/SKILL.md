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

**Token cost**: ~1,500 tokens (router + targeted section)

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
- `docs/agents/codegen-pipeline.md#overview` - Pipeline overview
- `docs/agents/codegen-pipeline.md#your-complete-ownership` - What you own

**TypeScript Model Design (Part 1)**:
- `docs/agents/codegen-pipeline.md#typescript-model-design` - Full Part 1
- `docs/agents/codegen-pipeline.md#model-locations` - File structure
- `docs/agents/codegen-pipeline.md#type-system-design-principles` - Design principles
- `docs/agents/codegen-pipeline.md#2-naming-standards` - **CRITICAL**: snake_case rules
- `docs/agents/codegen-pipeline.md#workflow-creating-new-node-types` - Workflow for new nodes
- `docs/agents/codegen-pipeline.md#quality-assurance-checklist` - Pre-submit checklist

**IR Builder System (Part 2)**:
- `docs/agents/codegen-pipeline.md#ir-builder-system` - Full Part 2
- `docs/agents/codegen-pipeline.md#ir-builder-architecture` - Directory structure
- `docs/agents/codegen-pipeline.md#pipeline-system` - BuildContext, BuildStep, orchestrator
- `docs/agents/codegen-pipeline.md#type-system` - UnifiedTypeConverter, type mappings
- `docs/agents/codegen-pipeline.md#ast-processing` - AST Walker, Filters, Extractors
- `docs/agents/codegen-pipeline.md#ir-generation-workflow` - Step-by-step IR generation

**Code Generation (Part 3)**:
- `docs/agents/codegen-pipeline.md#code-generation` - Full Part 3
- `docs/agents/codegen-pipeline.md#template-system` - Jinja templates
- `docs/agents/codegen-pipeline.md#generated-code-structure` - Output structure
- `docs/agents/codegen-pipeline.md#generation-workflow` - Complete make codegen workflow

**Diagnosis (Part 4)**:
- `docs/agents/codegen-pipeline.md#code-review-diagnosis` - Part 4 overview
- `docs/agents/codegen-pipeline.md#tracing-generation-issues` - Diagnosing generated code
- `docs/agents/codegen-pipeline.md#your-critical-responsibility` - Your unique role
- `docs/agents/codegen-pipeline.md#generation-vs-runtime-issues` - Generation vs runtime issues

**Workflows (Part 5)**:
- `docs/agents/codegen-pipeline.md#codegen-workflow` - Part 5 overview
- `docs/agents/codegen-pipeline.md#complete-workflow` - Full end-to-end steps
- `docs/agents/codegen-pipeline.md#validation-levels` - make apply vs apply-test
- `docs/agents/codegen-pipeline.md#critical-warnings` - Safety warnings

**Collaboration (Part 6)**:
- `docs/agents/codegen-pipeline.md#collaboration-escalation` - Part 6 overview
- `docs/agents/codegen-pipeline.md#collaboration-protocols` - Collaboration protocols
- `docs/agents/codegen-pipeline.md#when-to-engage-other-agents` - When to escalate

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
3. **If diagnosis needed**: Load critical-responsibility section, trace TypeScript → IR → Python
4. **If complex**: Escalate with `Task(dipeo-codegen-pipeline, "task details")`

## Critical Reminder

**You are the ONLY agent who diagnoses generated code internals.** If generated code looks wrong:
1. Load diagnosis section: `Skill(doc-lookup)` with `tracing-generation-issues`
2. Trace: TypeScript spec → IR JSON → Template → Generated Python
3. Escalate to agent if root cause is complex (IR builder bug, template issue)

---

**Token savings**: ~90% reduction (1,500 vs. 15,000 tokens) for focused tasks
