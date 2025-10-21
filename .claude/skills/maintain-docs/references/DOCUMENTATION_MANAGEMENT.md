# Documentation Management Guide

Guide for managing DiPeO's documentation to work optimally with doc-lookup skill and router skills.

## Quick Reference

```bash
# Preview what anchors would be added (dry-run)
make docs-add-anchors-dry

# Add anchors to features/formats/projects docs
make docs-add-anchors

# Generate anchor index for easy reference
make docs-anchor-index

# Validate router skills reference valid anchors
make docs-validate-anchors

# Complete documentation update (all above steps)
make docs-update
```

All scripts are in `.claude/skills/maintain-docs/scripts/` and can be run directly if needed.

## Architecture Overview

DiPeO uses a **progressive disclosure** documentation system:

```
Router Skills (50-100 lines)
    ↓ references
Documentation Anchors (#anchor-id)
    ↓ retrieved by
doc-lookup Skill
    ↓ returns
Targeted Sections (30-50 lines)
```

**Benefits**:
- 80-90% token reduction vs. loading full docs
- Single source of truth (docs in `docs/`, not duplicated in skills)
- Autonomous agents load only what they need
- No documentation drift

## Documentation Structure

```
docs/
├── agents/          # Agent-specific guides (router skills reference these)
│   ├── backend-development.md       ✅ 14 anchors
│   ├── package-maintainer.md        ✅ 14 anchors
│   ├── codegen-pipeline.md          ✅ 15 anchors
│   ├── frontend-development.md      ⚠️  Needs anchors
│   └── code-auditing.md             ⚠️  Needs anchors
│
├── architecture/    # System design docs
│   ├── README.md                    ✅ 10 anchors
│   └── detailed/
│       ├── graphql-layer.md         ✅ 7 anchors
│       ├── diagram-compilation.md   ⚠️  Needs anchors
│       └── memory_system_design.md  ⚠️  Needs anchors
│
├── features/        # Feature-specific guides
│   ├── mcp-server-integration.md    ⚠️  HIGH PRIORITY (20+ headings)
│   ├── diagram-to-python-export.md  ⚠️  Needs anchors
│   ├── webhook-integration.md       ⚠️  Needs anchors
│   └── claude-code-integration.md   ⚠️  Needs anchors
│
├── formats/         # Diagram format specs
│   ├── comprehensive_light_diagram_guide.md  ⚠️  HIGH PRIORITY (50+ headings)
│   └── diagram_formats.md           ⚠️  Needs anchors
│
└── projects/        # Project-specific workflows
    ├── code-generation-guide.md     ⚠️  Needs anchors
    ├── dipeocc-guide.md             ⚠️  Needs anchors
    └── frontend-enhance-guide.md    ⚠️  Needs anchors
```

**Status**: ~60/240+ headings have explicit anchors (25%)

## Anchor Naming Conventions

### Good Anchor Names

```markdown
## MCP Tool Registration {#mcp-tool-registration}
### Quick Start {#mcp-quick-start}
### CLI Flags Reference {#cli-flags}
#### Background Execution {#background-execution}
```

**Rules**:
1. Use kebab-case (lowercase with hyphens)
2. Be descriptive but concise
3. Include context prefix for disambiguation (e.g., `mcp-`, `cli-`, `handler-`)
4. Match auto-generated slug when possible for backward compatibility

### Bad Anchor Names

```markdown
## MCP Tool Registration {#mcp1}              ❌ Not descriptive
### Quick Start {#MCP-Quick-Start}            ❌ Not lowercase
### CLI Flags Reference {#the_cli_flags_ref}  ❌ Inconsistent style
```

## Adding Anchors to Documentation

### Step 1: Dry-run to Preview Changes

```bash
# Preview all changes at once (recommended)
make docs-add-anchors-dry

# Or check specific file/directory
python .claude/skills/maintain-docs/scripts/add_doc_anchors.py docs/features/mcp-server-integration.md --dry-run
python .claude/skills/maintain-docs/scripts/add_doc_anchors.py docs/features/ --recursive --dry-run
```

### Step 2: Apply Changes

```bash
# Add anchors to all features/formats/projects docs (recommended)
make docs-add-anchors

# Or add to specific file/directory
python .claude/skills/maintain-docs/scripts/add_doc_anchors.py docs/features/mcp-server-integration.md
python .claude/skills/maintain-docs/scripts/add_doc_anchors.py docs/features/ --recursive

# Add prefix for disambiguation (e.g., all anchors get 'mcp-' prefix)
python .claude/skills/maintain-docs/scripts/add_doc_anchors.py docs/features/mcp-server-integration.md --prefix mcp
```

### Step 3: Verify Changes

```bash
# View the diff
git diff docs/features/mcp-server-integration.md

# Test doc-lookup can find the new anchors
python .claude/skills/doc-lookup/scripts/section_search.py \
  --query "mcp-tool-registration" \
  --paths docs/features/mcp-server-integration.md \
  --top 1
```

### Step 4: Update Anchor Index

```bash
# Regenerate anchor index (markdown, recommended)
make docs-anchor-index

# Or generate JSON for programmatic access
python .claude/skills/maintain-docs/scripts/generate_anchor_index.py --json > .claude/data/anchors.json
```

## Creating Router Skills

Router skills should be **thin** (50-100 lines) and reference documentation anchors.

### Template Structure

```markdown
---
name: my-domain
description: Brief description of when to use this skill
allowed-tools: Read, Grep, Glob, Bash
---

# Domain Router Skill

## When to Use This Skill

Use this skill when:
- Specific scenario 1
- Specific scenario 2

**Don't use for**: Clear anti-patterns

## Decision Criteria

### Handle Directly (No Agent)
- Simple, single-file changes
- Well-documented patterns
- Configuration updates

### Use doc-lookup + Solve
- Need specific guidance on subtopic
- Multi-step but straightforward
- Implementation follows known pattern

### Escalate to Agent
- Complex, multi-file refactoring
- Architecture changes
- Unknown patterns or edge cases

## Key Documentation Sections

### Topic 1
- Overview: `docs/path/file.md#topic1-overview`
- Patterns: `docs/path/file.md#topic1-patterns`
- Examples: `docs/path/file.md#topic1-examples`

### Topic 2
- Guide: `docs/path/file.md#topic2-guide`
- Troubleshooting: `docs/path/file.md#topic2-troubleshooting`

## Lookup Procedure

1. Review decision criteria above
2. If need docs: `Skill(doc-lookup)` with anchor from list above
3. If still unclear: escalate to agent with `Task(agent-name)`

## Escalation Paths

- For X work → Use `agent-x`
- For Y work → Use `agent-y`
```

### Anchor Reference Best Practices

**Do**:
```markdown
### MCP Tools
- Registration: `docs/features/mcp-server-integration.md#mcp-tool-registration`
- Testing: `docs/features/mcp-server-integration.md#mcp-testing`
```

**Don't**:
```markdown
### MCP Tools
See docs/features/mcp-server-integration.md for details.  ❌ Not specific enough
```

## Maintenance Workflows

### When Adding New Documentation

1. Write documentation with explicit anchors from the start
2. If not added during writing: `make docs-add-anchors`
3. Add anchors to router skills if relevant
4. Update anchor index: `make docs-anchor-index`
5. Validate references: `make docs-validate-anchors`
6. Commit docs + anchor index together

### When Updating Documentation

1. Preserve existing anchors (don't change anchor IDs)
2. Add new anchors for new sections
3. Update router skills if anchors changed
4. Regenerate anchor index

### When Reorganizing Documentation

1. Keep anchor IDs stable (even if file moves)
2. Update router skill references to new paths
3. Add redirect comments in old locations if needed
4. Regenerate anchor index

## Validation & Quality Control

### Validate Anchors Are Reachable

```bash
# Validate all router skills (recommended)
make docs-validate-anchors

# Or validate specific skill
python .claude/skills/maintain-docs/scripts/validate_doc_anchors.py .claude/skills/dipeo-backend/SKILL.md
```

### Check for Broken References

```bash
# Find all doc references in router skills
grep -r "docs/" .claude/skills/*/SKILL.md

# Test each reference manually
python .claude/skills/doc-lookup/scripts/section_search.py \
  --query "anchor-id" \
  --paths docs/path/file.md
```

### Measure Token Efficiency

Compare token usage before/after using router skills:

```bash
# Before: Load full agent docs (auto-injection)
# Cost: ~15,000 tokens

# After: Router skill + doc-lookup
Skill(dipeo-backend)           # ~1,000 tokens (router)
Skill(doc-lookup) --query "cli-flags"  # ~500 tokens (section)
# Total: ~1,500 tokens (90% reduction)
```

## Common Patterns

### Pattern 1: Simple Task (No Docs Needed)

```
User: "Add --json flag to dipeo run"
→ Skill(dipeo-backend)          # Load router
→ Check decision criteria       # "Simple, follows known pattern"
→ Implement directly            # No need to load docs
```

### Pattern 2: Need Specific Guidance

```
User: "Add MCP resource for execution history"
→ Skill(dipeo-backend)          # Load router
→ Check decision criteria       # "Need MCP patterns"
→ Skill(doc-lookup) --query "mcp-resources"  # Load specific section
→ Implement following pattern
```

### Pattern 3: Complex Task (Agent Needed)

```
User: "Refactor CLI to support plugins"
→ Skill(dipeo-backend)          # Load router
→ Check decision criteria       # "Complex architecture change"
→ Task(dipeo-backend, "Refactor CLI...")  # Escalate to agent
   → Agent can load docs internally via doc-lookup as needed
```

## Troubleshooting

### Anchor Not Found

**Problem**: doc-lookup can't find expected anchor

**Solutions**:
1. Check anchor exists: `grep -r "anchor-id" docs/`
2. Try auto-generated slug instead: `#section-name`
3. Use keyword search: `--query "Section Name"`
4. Update anchor index: `make docs-anchor-index`

### Too Many Results

**Problem**: doc-lookup returns irrelevant sections

**Solutions**:
1. Use explicit anchor instead of keyword
2. Narrow search with `--paths` to specific file
3. Make query more specific
4. Add context prefix to anchors (e.g., `mcp-`, `cli-`)

### Section Truncated

**Problem**: doc-lookup only shows first 30 lines

**Solutions**:
1. Increase `--max-lines`: `--max-lines 100`
2. Use `Read` tool with specific line range
3. Break large sections into smaller subsections with their own anchors

## Future Enhancements

### Planned Features

- **Granular sub-skills**: Domain-specific router skills (e.g., `backend-cli`, `backend-mcp`)
- **Anchor suggestions**: Suggest similar anchors when exact match not found
- **Section dependencies**: Map which sections reference others
- **Automated sync**: Detect when docs change and validate router skills still work

### Extension Ideas

- **Anchor aliases**: Support multiple anchors for same section
- **Cross-references**: Auto-detect when sections reference others
- **Usage analytics**: Track which anchors are most frequently accessed
- **Version tracking**: Maintain anchor changelog for major refactorings

## Related Documentation

- [Agent Documentation Index](agents/index.md) - Overview of agent documentation access pattern
- [doc-lookup Skill](.claude/skills/doc-lookup/SKILL.md) - Detailed doc-lookup usage guide
- [Router Skill Examples](.claude/skills/) - See dipeo-backend, dipeo-package-maintainer, etc.

## Quick Command Reference

```bash
# Makefile commands (recommended)
make docs-add-anchors-dry     # Preview anchor additions
make docs-add-anchors         # Add anchors to docs
make docs-anchor-index        # Generate anchor index
make docs-validate-anchors    # Validate router skills
make docs-update              # Complete update (all above)

# Direct script usage (for custom paths or options)
python .claude/skills/maintain-docs/scripts/add_doc_anchors.py <path> [--dry-run] [--recursive] [--prefix <prefix>]
python .claude/skills/maintain-docs/scripts/generate_anchor_index.py [--json] > output.md
python .claude/skills/maintain-docs/scripts/validate_doc_anchors.py [skill_files...]

# Search documentation (doc-lookup skill)
python .claude/skills/doc-lookup/scripts/section_search.py \
  --query <anchor-or-keyword> \
  --paths <file-or-dir> \
  --top <N> [--max-lines <N>] [--no-content]
```
