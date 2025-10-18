---
name: fix-typecheck
description: Fix TypeScript type checking errors from pnpm typecheck, analyze type mismatches, and resolve type safety issues in React and TypeScript applications. Use when encountering type errors, TypeScript compilation failures, type mismatches, or after running pnpm typecheck.
---

# TypeScript Type Error Fixer

Fix TypeScript type checking errors in React and modern web applications. Analyze type mismatches, resolve type safety issues, and maintain proper typing.

## Core Workflow

1. **Run** `pnpm typecheck` → Get error list
2. **Group** related errors by common cause
3. **Fix** from most fundamental → derived errors
4. **Re-run** `pnpm typecheck` after significant fixes
5. **Verify** no new errors introduced

## Fixing Principles

- **Fix at source**, not with type assertions
- **Maintain type safety** - never use `any` unless absolutely necessary and well-justified
- **Prefer** union types, generics, and proper type narrowing over loose typing
- **Update** type definitions, interfaces, or generic constraints as needed
- **Preserve** existing functionality while fixing types

## Common Patterns

Identify and fix:
- Missing/incorrect generic type parameters
- Incompatible prop types (parent ↔ child)
- Event handler signatures
- GraphQL query result mismatches
- Missing null/undefined checks
- Discriminated union issues
- Array method type inference

**Frontend specifics**: React props, hooks constraints, event handlers, GraphQL types, Zustand stores, React Query

## DiPeO-Specific

- **Generated code** (`dipeo/diagram_generated/`) → Don't edit, trace to source spec
- **GraphQL types** mismatched → Run `make graphql-schema`
- **Multiple components** same error → Fix shared type definition
- **Quick fix** compromises safety → Implement proper solution

## Quality Checks

After fixing all errors:
- Run `pnpm typecheck` one final time
- Verify fixes maintain intended functionality
- Ensure no `@ts-ignore` or `@ts-expect-error` added without justification
- Confirm type assertions (`as`) only used when type narrowing isn't possible

Always prioritize long-term type safety over quick fixes.
