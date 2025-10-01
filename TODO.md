# DiPeO Project Todos

## 📋 Next Up

**Recommended Starting Point**: Consider starting with Medium Priority tasks (Phase 3: Code Quality improvements)

---

## High Priority (Start Here)

_(No high priority tasks currently pending)_

## Medium Priority

### TypeScript Models - Phase 3: Code Quality (P2)

- [ ] Create reusable GraphQL field fragments for common structures
  - Location: `dipeo/models/src/frontend/query-definitions/`
  - Structures to Fragment: Position (x, y), LLMConfig (provider, model, temperature, etc.), Metadata (created_at, updated_at, tags, etc.)
  - Goal: Reduce duplication in GraphQL queries and mutations
  - Estimated Effort: Medium
  - Benefits:
    - DRY principle in GraphQL definitions
    - Easier to maintain consistent field selections
    - Smaller generated code footprint

- [ ] Add TypeScript path aliases to tsconfig.json
  - Location: `dipeo/models/tsconfig.json`
  - Aliases to Add: `@core/*` → `src/core/*`, `@nodes/*` → `src/node-specs/*`, `@frontend/*` → `src/frontend/*`, `@utilities/*` → `src/utilities/*`
  - Goal: Cleaner imports, better organization
  - Estimated Effort: Small

- [ ] Update all imports to use new path aliases
  - Location: Throughout `dipeo/models/src/`
  - Goal: Replace relative imports with alias-based imports
  - Estimated Effort: Medium
  - Dependencies: Requires path aliases to be added to tsconfig.json
  - Note: Can be partially automated with find/replace

- [ ] Add branded type helper functions
  - Location: `dipeo/models/src/core/` or new `src/utilities/branded-types.ts`
  - Helpers to Create: `createNodeID(id: string): NodeID`, `createPersonID(id: string): PersonID`, `createDiagramID(id: string): DiagramID`, `createMemoryID(id: string): MemoryID`
  - Goal: Type-safe branded type construction with runtime validation
  - Estimated Effort: Small
  - Benefits:
    - Single place to add validation logic for IDs
    - Prevents accidentally mixing different ID types
    - Better developer ergonomics

## Low Priority / Future Enhancements

### TypeScript Models - Phase 4: Polish (P3)

- [ ] Refactor exports in index.ts for better tree-shaking
  - Location: `dipeo/models/src/index.ts`
  - Current State: May have inefficient barrel exports
  - Goal: Optimize exports to enable better tree-shaking in consuming applications
  - Estimated Effort: Small
  - Implementation Notes:
    - Review current export structure
    - Ensure named exports are used where appropriate
    - Document export strategy for future maintainers

- [ ] Add JSDoc documentation to all node spec files
  - Location: All files in `dipeo/models/src/node-specs/`
  - Coverage Needed: Node spec interfaces and types, field definitions and their purposes, enum values and their meanings, complex configuration objects
  - Goal: Improve developer experience and code understanding
  - Estimated Effort: Large
  - Benefits:
    - Better IDE autocomplete and hover information
    - Easier onboarding for new contributors
    - Self-documenting code
  - Note: Can be done incrementally, one spec at a time

## In Progress

_(No tasks currently in progress)_

---

## Completed Archive

<details>
<summary>Click to view recently completed tasks (2025-10-01)</summary>

- [x] Consolidate field defaults into node specs (2025-10-01)
  - Phase 2: Runtime Safety - TypeScript Models
  - Migrated all default values from FIELD_SPECIAL_HANDLING into individual node specs
  - Each field with a default now has `defaultValue` property directly in its spec
  - Fixed spec_parser.py bug: now correctly renames `defaultValue` to `default` for templates
  - Regenerated all code successfully with `make codegen` and `make apply-test`
  - Result: Single source of truth for defaults, cleaner separation of concerns

- [x] Generate Zod schemas from node specifications (2025-10-01)
  - Location: `projects/codegen/templates/frontend/zod_schemas_models.j2`
  - Implementation: Created new Jinja2 template for Zod schema generation
  - Output: Generates to `dipeo/models/src/__generated__/schemas.ts`
  - Integration: Added to `generate_frontend_simplified.light.yaml` pipeline
  - Features: Individual node schemas, type definitions, schema registry, validation helpers
  - Successfully tested with `make codegen`
  - Includes proper validation rules (min/max, regex patterns, etc.)

- [x] Export generated Zod schemas from @dipeo/models package (2025-10-01)
  - Location: `dipeo/models/src/index.ts`
  - Implementation: Added export statement for generated schemas
  - Result: Schemas now available via `import { ... } from '@dipeo/models'`
  - Package builds successfully with `pnpm build`
  - Enables runtime validation in consuming applications

- [x] Fix NODE_TYPE_MAP synchronization - add missing IR_BUILDER and DIFF_PATCH entries (2025-10-01)
  - Fixed by refactoring to auto-generate from NodeType enum
  - No manual entries were needed as types were already present

- [x] Generate NODE_TYPE_MAP automatically from NodeType enum (2025-10-01)
  - Location: `dipeo/models/src/utilities/conversions.ts`
  - Implemented using Object.values().reduce() for automatic generation
  - Eliminates manual maintenance and prevents future synchronization issues
  - TypeScript build passed successfully

</details>

---

## Notes

### TypeScript Models & Code Generation
- **Codegen Impact**: Most TypeScript model tasks will require running `make codegen` after implementation
- **Testing**: Each task should be validated with `make apply-test` before applying
- **Documentation**: Update `/docs/projects/code-generation-guide.md` if codegen pipeline changes
- **Breaking Changes**: Tasks marked with priority P0 or P1 may require coordinated updates across the codebase

### Related Documentation
- [Code Generation Guide](docs/projects/code-generation-guide.md)
- [Overall Architecture](docs/architecture/overall_architecture.md)
- [Models Package](dipeo/models/)
