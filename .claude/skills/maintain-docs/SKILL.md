---
name: maintain-docs
description: Update and maintain documentation to reflect current implementation after code changes, refactoring, or new features. Remove temporal language, verify accuracy against code, and keep docs current. Use when updating docs, syncing documentation, removing outdated info, or after implementing features.
---

# Documentation Maintainer

This guide is for maintaining clean, accurate, and implementation-focused documentation. The goal is to ensure documentation always reflects the current state of the system without accumulating historical cruft or verbose change descriptions.

## Core Principles

1. **Present State Focus**: Describe what IS implemented, not what WAS changed. Remove all temporal language like "now supports", "recently added", "updated to include"
2. **No Changelog Pollution**: Changes belong in git history, not in feature descriptions
3. **Clarity Over Completeness**: Prefer concise, clear descriptions over exhaustive detail. Every sentence must add value
4. **Implementation Truth**: Verify claims against actual code before documenting
5. **Single Source of Truth**: Each piece of information should exist in exactly one canonical location. Use cross-references instead of duplicating content

## Update Workflow

When updating documentation:

1. **Audit Current State**: Verify what is actually implemented in the codebase
2. **Remove Temporal Language**: Eliminate phrases like:
   - "Recently added" / "Now supports"
   - "Updated to include" / "New feature"
   - "As of version X"
3. **Consolidate Redundancy**: Merge duplicate information, remove repetitive explanations
4. **Verify Accuracy**: Cross-reference documentation claims with actual code implementation
5. **Maintain Structure**: Preserve existing organization unless restructuring improves clarity

## Content Standards

**Good Documentation**:
- "The service registry provides type categorization, audit trails, and production safety features"
- "Node handlers are located in `/dipeo/application/execution/handlers/`"
- "Use `dipeo run [diagram] --debug` for detailed execution logs"

**Bad Documentation**:
- "The service registry was recently enhanced to add type categorization and audit trails"
- "We've updated the node handlers to support new features"
- "The debug flag has been improved to provide better logging"

## Handling Different Documentation Types

**Architecture Docs**: Focus on current design, component relationships, and key decisions. Remove migration notes once migrations are complete.

**User Guides**: Provide clear, actionable instructions for current functionality. Remove outdated workflows.

**API Documentation**: Describe current endpoints, parameters, and responses. Remove deprecated API references unless explicitly marked.

**README Files**: Keep concise with essential setup, usage, and reference information.

## Quality Checklist

Before finalizing updates:
- ✓ Describes current implementation?
- ✓ Verifiable in codebase?
- ✓ Temporal language removed?
- ✓ Simplest accurate description?
- ✓ Adds unique value?
- ✓ Not duplicating content from elsewhere?

## Red Flags to Remove

- Historical narratives ("First we did X, then we added Y")
- Version-specific notes ("In v2.0 we changed...")
- Redundant examples that don't add clarity
- Overly detailed explanations of obvious concepts
- Apologetic or uncertain language ("This might...", "Hopefully...")

## Edge Cases

- **Deprecated Features**: Mark clearly as deprecated with migration path, but keep concise
- **Experimental Features**: Label as experimental, describe current state, avoid speculation
- **Missing Documentation**: Create minimal necessary documentation, focusing on essential usage
- **Conflicting Information**: Verify against code, update to match implementation truth

The goal is documentation that serves developers efficiently, accurately reflects the current system, and requires minimal maintenance because it focuses on timeless implementation details rather than temporal changes.
