---
name: clean-comments
description: Remove unnecessary, redundant, or obvious code comments while preserving valuable explanations. Use when cleaning up comments, removing verbose documentation, simplifying inline comments, or preparing code for review.
---

# Comment Cleanup

This guide is for removing unnecessary, redundant, or obvious code comments while preserving valuable explanations. Use this when cleaning up verbose documentation or preparing code for review.

## Core Principles

1. **Remove obvious comments**: Delete comments that merely restate what the code clearly does (e.g., '// increment counter' above 'counter++')
2. **Keep complexity explanations**: Preserve comments at decision points, complex algorithms, or non-obvious implementations
3. **Brevity for members**: Keep class and function documentation concise - one line when possible, focusing on the 'why' not the 'what'
4. **Deprecation selectivity**: Remove deprecated/outdated code comments unless they provide critical migration context
5. **Trust readable code**: If function names and parameters clearly convey purpose, additional explanation is redundant

## Review Criteria

When reviewing code, ask yourself:
- Does this comment add value beyond what well-named code already communicates?
- Does it explain business logic, edge cases, or architectural decisions? → **Keep**
- Could this comment block be reduced to a single meaningful line? → **Simplify**
- Is this a TODO/FIXME comment referencing completed work? → **Remove**
- Would this help a new developer understand non-obvious behavior? → **Keep**

## Batch Processing

- Process **max 15 files per session** for manageable reviews
- Focus on clarity through code structure rather than excessive documentation
- Preserve only high-value comments that answer questions the code cannot

## Output

The output should be the cleaned code with only high-value comments remaining. Each preserved comment should answer questions that the code itself cannot.

**Remember**: The best comment is often no comment when the code speaks for itself.
