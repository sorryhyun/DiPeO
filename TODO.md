# DiPeO Project Todos

---

## Current Tasks

_No active tasks. See Future Enhancements below for potential improvements._

---

## Future Enhancements

### Granular Domain Skills
Create more focused router skills for specific sub-domains:
- `backend-cli`: CLI-specific guidance (~30 lines)
- `backend-mcp`: MCP server-specific guidance (~30 lines)
- `backend-db`: Database-specific guidance (~30 lines)
- `codegen-typescript`: TypeScript model design patterns
- `codegen-ir`: IR builder implementation
- `codegen-graphql`: GraphQL schema generation

### Enhanced doc-lookup Features
- Support for including multiple sections in one query
- Anchor suggestion when exact match not found
- Section dependency graph (e.g., "handler patterns" → "service architecture")

### Skill Composition
- Allow skills to reference prerequisite skills
- Build skill dependency chains for complex topics

### Automated Sync
- Script to detect when `docs/agents/*.md` changes
- Validate router skills still reference valid anchors
- CI/CD integration for documentation validation

---

## Completed (2025-10-19)

### Documentation Anchor Coverage ✅

**Summary**: Added comprehensive explicit anchors to all documentation files to enable efficient doc-lookup skill usage.

**Key Achievements**:
- ✅ Added 641 anchors across 21 documentation files
  - Features: 197 anchors across 7 files
  - Formats: 76 anchors across 2 files
  - Projects: 162 anchors across 4 files
  - Agents: 206 anchors across 7 files (total now 313 anchors)
- ✅ Fixed all 12 broken anchor references in router skills
- ✅ All 68 anchor references now valid (0 broken)

**Files Updated**:
- `.claude/skills/dipeo-codegen-pipeline/SKILL.md` - Fixed 5 broken anchor refs
- `.claude/skills/dipeo-package-maintainer/SKILL.md` - Fixed 4 broken anchor refs
- `.claude/skills/doc-lookup/SKILL.md` - Fixed 3 broken anchor refs

**Impact**:
- doc-lookup skill can now precisely locate any documentation section
- Router skills have stable, validated anchor references
- 641 anchors provide fine-grained documentation access

---

### Agent Documentation Migration: PreToolUse Hook → Skills ✅

**Summary**: Migrated from automatic documentation injection to on-demand skill-based loading using thin router skills + doc-lookup.

**Key Achievements**:
- 80-90% token reduction (1,500 vs 15,000 tokens per task)
- Created 3 router skills (dipeo-backend, dipeo-package-maintainer, dipeo-codegen-pipeline)
- Added 60 stable anchors to agent/architecture documentation
- Removed PreToolUse hook, archived injection script
- Updated CLAUDE.md and docs/agents/index.md with new patterns

**Infrastructure Created**:
- `.claude/skills/doc-lookup/` - Section search by anchor/keyword
- `.claude/skills/maintain-docs/` - Documentation maintenance with helper scripts
  - `scripts/add_doc_anchors.py` - Add anchors to markdown files
  - `scripts/validate_doc_anchors.py` - Validate router skill references
  - `references/DOCUMENTATION_MANAGEMENT.md` - Complete documentation management guide
- Makefile targets: `docs-add-anchors`, `docs-validate-anchors`, `docs-update`

---

_Use `/dipeotodos` to view this file anytime._
