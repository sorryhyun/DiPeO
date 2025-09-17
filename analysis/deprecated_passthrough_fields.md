# GraphQL Deprecated Passthrough Fields Analysis

## Overview
This document identifies GraphQL result types that still depend on deprecated passthrough fields (`diagram`, `node`, `person`, `api_key`, `execution`) and their usage across the codebase.

## Deprecated Fields in Result Types

### 1. DiagramResult
- **Deprecated Field**: `diagram` (should use `data`)
- **File**: `dipeo/diagram_generated/graphql/results.py:95-98`
- **Auto-populated**: Yes, in `__post_init__` method

### 2. NodeResult
- **Deprecated Field**: `node` (should use `data`)
- **File**: `dipeo/diagram_generated/graphql/results.py:129-132`
- **Auto-populated**: Yes, in `__post_init__` method

### 3. ExecutionResult
- **Deprecated Field**: `execution` (should use `data`)
- **File**: `dipeo/diagram_generated/graphql/results.py:162-165`
- **Auto-populated**: Yes, in `__post_init__` method

### 4. PersonResult
- **Deprecated Field**: `person` (should use `data`)
- **File**: `dipeo/diagram_generated/graphql/results.py:196-199`
- **Auto-populated**: Yes, in `__post_init__` method

### 5. ApiKeyResult
- **Deprecated Field**: `api_key` (should use `data`)
- **File**: `dipeo/diagram_generated/graphql/results.py:229-232`
- **Auto-populated**: Yes, in `__post_init__` method

## Frontend Usage

### Generated Query Definitions
The following files still reference deprecated fields in GraphQL queries:

**apps/web/src/__generated__/queries/all-queries.ts**:
- Line 325: `api_key {`
- Line 389: `diagram {`
- Line 407, 434, 462: `execution {`
- Line 522: `node {`
- Line 570, 587: `person {`

**apps/web/src/__generated__/graphql.tsx**:
- Line 2069: `api_key {`
- Line 2248: `diagram {`
- Line 2289, 2362, 2436: `execution {`
- Line 2614: `node {`
- Line 2732, 2771: `person {`

## Backend Usage

### Application Layer Direct Assignment
The following resolvers still assign to deprecated fields:

**dipeo/application/graphql/schema/mutations/execution.py**:
- Lines 119, 166, 211, 242: `result.execution = execution`

**dipeo/application/graphql/schema/mutations/diagram.py**:
- Lines 170, 179: `result.diagram = domain_diagram`

## Migration Strategy

### Phase 1: Template Refactoring
- Refactor `strawberry_results.j2` to consolidate `BaseResultMixin`
- Ensure `from_envelope` and `success_result` methods handle data assignment uniformly
- Keep deprecated fields with compatibility shims for now

### Phase 2: Frontend Migration
- Update TypeScript query definitions to use `data` field instead of entity-specific fields
- Regenerate GraphQL queries and hooks
- Update component code to access `data` field

### Phase 3: Backend Migration
- Remove direct assignment to deprecated fields in resolvers
- Use only `data` field for all entity returns
- Rely on `__post_init__` for backward compatibility during transition

### Phase 4: Final Cleanup
- Remove deprecated field definitions from templates
- Remove `__post_init__` auto-population logic
- Complete validation of all endpoints

## Notes
- All deprecated fields are marked with `deprecation_reason="Use 'data' field instead"`
- Auto-population via `__post_init__` provides backward compatibility
- Both frontend and backend need updates before deprecated fields can be fully removed
