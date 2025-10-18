---
name: maintain-docs
description: Update and maintain documentation to reflect current implementation after code changes, refactoring, or new features. Remove temporal language, verify accuracy against code, and keep docs current. Use when updating docs, syncing documentation, removing outdated info, or after implementing features.
---

# Documentation Maintainer

Maintain clean, accurate, implementation-focused documentation. Ensure docs always reflect current state without historical cruft or verbose change descriptions.

## Core Principles

1. **Present State Focus**: Describe what IS implemented, not what WAS changed. Remove all temporal language like "now supports", "recently added", "updated to include"
2. **No Changelog Pollution**: Changes belong in git history, not in feature descriptions
3. **Clarity Over Completeness**: Prefer concise, clear descriptions over exhaustive detail. Every sentence must add value
4. **Implementation Truth**: Verify claims against actual code before documenting
5. **Single Source of Truth**: Each piece of information should exist in exactly one canonical location. Use cross-references instead of duplicating content

## Update Workflow

1. **Audit**: Verify what's actually implemented
2. **Remove temporal language**: "Recently added", "Now supports", "Updated to", "As of version X"
3. **Consolidate**: Merge duplicates, remove repetition
4. **Verify**: Cross-reference with actual code
5. **Maintain structure**: Preserve organization unless improvement needed

## Content Standards

**Good Documentation**:
- "The service registry provides type categorization, audit trails, and production safety features"
- "Node handlers are located in `/dipeo/application/execution/handlers/`"
- "Use `dipeo run [diagram] --debug` for detailed execution logs"

**Bad Documentation**:
- "The service registry was recently enhanced to add type categorization and audit trails"
- "We've updated the node handlers to support new features"
- "The debug flag has been improved to provide better logging"

## Documentation Types

**Architecture**: Current design, relationships, decisions. Remove completed migration notes.

**User Guides**: Clear instructions for current functionality. Remove outdated workflows.

**API Docs**: Current endpoints, parameters, responses. Remove deprecated APIs unless marked.

**READMEs**: Concise setup, usage, and reference.

## Quality Checklist

Before finalizing updates:
- ✓ Describes current implementation?
- ✓ Verifiable in codebase?
- ✓ Temporal language removed?
- ✓ Simplest accurate description?
- ✓ Adds unique value?
- ✓ Not duplicating content from elsewhere?

## Red Flags

Remove:
- Historical narratives ("First we did X, then Y")
- Version notes ("In v2.0 we changed...")
- Redundant examples
- Overly detailed obvious concepts
- Apologetic language ("This might...", "Hopefully...")

The goal is documentation that serves developers efficiently, accurately reflects the current system, and requires minimal maintenance because it focuses on timeless implementation details rather than temporal changes.
