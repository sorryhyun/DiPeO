# Deprecated Scripts

This directory contains scripts that have been deprecated and are no longer in active use.

## inject-agent-docs.py

**Deprecated**: 2025-10-19
**Replaced by**: Router skills + doc-lookup pattern

### Why Deprecated

The automatic documentation injection via PreToolUse hook had several limitations:

1. **Token inefficiency**: Injected 12k-20k tokens per agent invocation (entire doc sets)
2. **All-or-nothing**: Loaded complete documentation even when only small sections needed
3. **No agent autonomy**: Orchestrator decided what docs to load, not the agent
4. **Content duplication risk**: Could lead to drift between injected docs and source files

### Migration Path

The new approach uses:

1. **Router skills** (~50-100 lines): Provide decision criteria + stable documentation anchors
   - `Skill(dipeo-backend)`
   - `Skill(dipeo-package-maintainer)`
   - `Skill(dipeo-codegen-pipeline)`

2. **Doc-lookup skill**: Extract specific sections by anchor/keyword on-demand
   - `Skill(doc-lookup)` with `--query "section-anchor"`
   - Progressive disclosure: Load only what's needed

### Benefits

- **80-90% token reduction**: ~1,500 tokens vs. ~15,000 tokens per task
- **Agent autonomy**: Agents request context when needed
- **Single source of truth**: Docs remain in `docs/`, skills just reference them
- **No drift**: Skills use stable anchors, don't duplicate content
- **Composability**: Can layer skills as investigation deepens

### Usage Pattern

```python
# OLD: Automatic injection (deprecated)
Task(dipeo-backend, "Fix CLI bug")
# → PreToolUse hook injects ALL backend docs (2,000+ lines)
# → Cost: 15,000 tokens

# NEW: Progressive disclosure
Skill(dipeo-backend)  # Load 50-line router
# → Review decision criteria
# → Determine: need specific CLI section
# → Skill(doc-lookup) with --query "cli-commands"
# → Get targeted section only (~50 lines)
# → Cost: ~1,500 tokens (90% reduction)
```

### Documentation

See `TODO.md` section "Agent Documentation Migration: PreToolUse Hook → Skills" for complete migration details.

### History

- **Created**: 2024
- **Deprecated**: 2025-10-19
- **Removed from**: `.claude/settings.local.json` (PreToolUse hook)
- **Status**: Archived but functional if hook is restored
