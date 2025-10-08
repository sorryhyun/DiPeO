# TODO - @dipeo/models TypeScript Domain Model Improvements

This file tracks improvements to the TypeScript domain models that generate the Python backend code.

---

## Phase 1: Critical Fixes (P0)

### NODE_TYPE_MAP Synchronization & Automation
- [ ] Fix NODE_TYPE_MAP synchronization - add missing IR_BUILDER and DIFF_PATCH entries
  - **Location**: `dipeo/models/src/utilities/conversions.ts`
  - **Issue**: Map is manually maintained and missing entries for newer node types
  - **Priority**: High - causes runtime errors when these node types are used
  - **Estimated Effort**: Small

- [ ] Generate NODE_TYPE_MAP automatically from NodeType enum
  - **Location**: `dipeo/models/src/utilities/conversions.ts`
  - **Current State**: Manual mapping that can get out of sync with enum
  - **Goal**: Auto-generate mapping from NodeType enum to eliminate manual maintenance
  - **Priority**: High - prevents future synchronization issues
  - **Estimated Effort**: Medium
  - **Dependencies**: Requires codegen pipeline update

- [ ] Automate node registry with auto-discovery system
  - **Location**: `dipeo/models/src/node-specs/node-registry.ts`
  - **Current State**: Manual imports and exports for each node spec
  - **Goal**: Replace with auto-discovery system that finds all node specs automatically
  - **Priority**: High - reduces maintenance burden for new node types
  - **Estimated Effort**: Large
  - **Implementation Notes**:
    - Consider glob-based discovery of node spec files
    - Maintain type safety while automating
    - Update build process to support auto-discovery

---

## Phase 2: Runtime Safety (P1)

### Zod Schema Generation & Validation
- [ ] Generate Zod schemas from node specifications
  - **Location**: New codegen step in code generation pipeline
  - **Goal**: Auto-generate Zod schemas for runtime validation from TypeScript specs
  - **Priority**: Medium - adds runtime type safety
  - **Estimated Effort**: Large
  - **Benefits**:
    - Runtime validation of diagram data
    - Better error messages for invalid diagrams
    - Type safety at runtime, not just compile time
  - **Implementation Notes**:
    - Add new IR builder for Zod schemas
    - Generate schemas alongside Python Pydantic models
    - Consider ts-to-zod or similar tooling

- [ ] Export generated Zod schemas from @dipeo/models package
  - **Location**: `dipeo/models/src/index.ts`
  - **Goal**: Make Zod schemas available for import and use
  - **Priority**: Medium
  - **Estimated Effort**: Small
  - **Dependencies**: Requires Zod schema generation task to be completed

### Field Defaults Consolidation
- [ ] Consolidate field defaults into node specs
  - **Location**: Move from `dipeo/models/src/utilities/field-special-handling.ts` into individual node specs
  - **Current State**: Defaults are defined separately in FIELD_SPECIAL_HANDLING
  - **Goal**: Single source of truth for default values within node specs themselves
  - **Priority**: Medium - improves maintainability
  - **Estimated Effort**: Medium
  - **Implementation Notes**:
    - Update node spec interface to support default values
    - Migrate existing defaults from FIELD_SPECIAL_HANDLING
    - Update codegen to use spec-defined defaults
    - Consider backward compatibility during migration

---

## Phase 3: Code Quality (P2)

### GraphQL Optimization
- [ ] Create reusable GraphQL field fragments for common structures
  - **Location**: `dipeo/models/src/frontend/query-definitions/`
  - **Structures to Fragment**:
    - Position (x, y)
    - LLMConfig (provider, model, temperature, etc.)
    - Metadata (created_at, updated_at, tags, etc.)
  - **Goal**: Reduce duplication in GraphQL queries and mutations
  - **Priority**: Low - code quality improvement
  - **Estimated Effort**: Medium
  - **Benefits**:
    - DRY principle in GraphQL definitions
    - Easier to maintain consistent field selections
    - Smaller generated code footprint

### TypeScript Module Organization
- [ ] Add TypeScript path aliases to tsconfig.json
  - **Location**: `dipeo/models/tsconfig.json`
  - **Aliases to Add**:
    - `@core/*` → `src/core/*`
    - `@nodes/*` → `src/node-specs/*`
    - `@frontend/*` → `src/frontend/*`
    - `@utilities/*` → `src/utilities/*`
  - **Goal**: Cleaner imports, better organization
  - **Priority**: Low - developer experience improvement
  - **Estimated Effort**: Small

- [ ] Update all imports to use new path aliases
  - **Location**: Throughout `dipeo/models/src/`
  - **Goal**: Replace relative imports with alias-based imports
  - **Priority**: Low
  - **Estimated Effort**: Medium
  - **Dependencies**: Requires path aliases to be added to tsconfig.json
  - **Note**: Can be partially automated with find/replace

### Type Safety Improvements
- [ ] Add branded type helper functions
  - **Location**: `dipeo/models/src/core/` or new `src/utilities/branded-types.ts`
  - **Helpers to Create**:
    - `createNodeID(id: string): NodeID`
    - `createPersonID(id: string): PersonID`
    - `createDiagramID(id: string): DiagramID`
    - `createMemoryID(id: string): MemoryID`
  - **Goal**: Type-safe branded type construction with runtime validation
  - **Priority**: Low - enhanced type safety
  - **Estimated Effort**: Small
  - **Benefits**:
    - Single place to add validation logic for IDs
    - Prevents accidentally mixing different ID types
    - Better developer ergonomics

---

## Phase 4: Polish (P3)

### Export Optimization
- [ ] Refactor exports in index.ts for better tree-shaking
  - **Location**: `dipeo/models/src/index.ts`
  - **Current State**: May have inefficient barrel exports
  - **Goal**: Optimize exports to enable better tree-shaking in consuming applications
  - **Priority**: Low - bundle size optimization
  - **Estimated Effort**: Small
  - **Implementation Notes**:
    - Review current export structure
    - Ensure named exports are used where appropriate
    - Document export strategy for future maintainers

### Documentation
- [ ] Add JSDoc documentation to all node spec files
  - **Location**: All files in `dipeo/models/src/node-specs/`
  - **Coverage Needed**:
    - Node spec interfaces and types
    - Field definitions and their purposes
    - Enum values and their meanings
    - Complex configuration objects
  - **Goal**: Improve developer experience and code understanding
  - **Priority**: Low - documentation enhancement
  - **Estimated Effort**: Large
  - **Benefits**:
    - Better IDE autocomplete and hover information
    - Easier onboarding for new contributors
    - Self-documenting code
  - **Note**: Can be done incrementally, one spec at a time

---

## Completed Tasks

*No tasks completed yet*

---

## Notes

- **Codegen Impact**: Most tasks will require running `make codegen` after implementation
- **Testing**: Each task should be validated with `make apply-test` before applying
- **Documentation**: Update `/docs/projects/code-generation-guide.md` if codegen pipeline changes
- **Breaking Changes**: Tasks marked with priority P0 or P1 may require coordinated updates across the codebase

## Related Documentation

- [Code Generation Guide](docs/projects/code-generation-guide.md)
- [Overall Architecture](/home/sorryhyun/PycharmProjects/DiPeO/docs/architecture/overall_architecture.md)
- [Models Package](/home/sorryhyun/PycharmProjects/DiPeO/dipeo/models/)
