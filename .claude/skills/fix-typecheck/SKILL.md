---
name: fix-typecheck
description: Fix TypeScript type checking errors from pnpm typecheck, analyze type mismatches, and resolve type safety issues in React and TypeScript applications. Use when encountering type errors, TypeScript compilation failures, type mismatches, or after running pnpm typecheck.
---

# TypeScript Type Error Fixer

This guide is for fixing TypeScript type checking errors in React and modern web applications. It covers analyzing type mismatches, resolving type safety issues, and maintaining proper typing throughout the codebase.

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

## Common Pattern Recognition

Common type errors to identify and fix:
- Missing or incorrect generic type parameters
- Incompatible prop types between parent and child components
- Incorrect event handler signatures
- Type mismatches in GraphQL query results
- Missing null/undefined checks in optional chaining
- Incorrect discriminated union usage
- Type inference issues with array methods

## Frontend-Specific Expertise

Key frontend typing concepts:
- React component prop types and their proper definition
- React hooks and their type constraints
- Event handler types and DOM type definitions
- GraphQL generated types and their integration
- Zustand store typing patterns
- React Query type patterns

## Project-Specific Context

This is a DiPeO project with:
- Generated code in `dipeo/diagram_generated/` (don't manually edit)
- GraphQL types that may need regeneration via `make graphql-schema`
- Domain-driven structure in `/apps/web/src/domain/`
- Infrastructure code in `/apps/web/src/infrastructure/`
- Centralized Zustand store patterns

## Decision Framework

- If type error involves **generated code** → Trace back to source specification
- If **GraphQL types** are mismatched → Consider schema regeneration
- If **multiple components** share same error → Fix the shared type definition
- If quick fix would **compromise type safety** → Implement proper solution instead

## Quality Checks

After fixing all errors:
- Run `pnpm typecheck` one final time
- Verify fixes maintain intended functionality
- Ensure no `@ts-ignore` or `@ts-expect-error` added without justification
- Confirm type assertions (`as`) only used when type narrowing isn't possible

Always prioritize long-term type safety over quick fixes.
