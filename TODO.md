# DiPeO Project Todos

Last updated: 2025-10-12

## Overview

This document tracks the comprehensive deprecation removal plan for DiPeO. The goal is to systematically remove all deprecated code across TypeScript models, Python backend, GraphQL schema, and infrastructure.

**Current Status:**
- Phase 1 (TypeScript Model Deprecations): COMPLETED (6/6 tasks)
- Phase 2 (Python Backend Deprecations): COMPLETED (5/5 tasks)
- Phase 3 (GraphQL Schema Deprecations): COMPLETED (4/4 tasks)
- Phase 4 (Infrastructure Cleanup): Not started (0/3 tasks)
- Phase 5 (Documentation Updates): Not started (0/2 tasks)
- Phase 6 (NPM Package Deprecations): Not started (0/2 tasks - Optional/Low Priority)
- Phase 7 (Testing & Validation): Not started (0/4 tasks)

**Total Tasks:** 25 tasks (23 required + 2 optional)
**Completed:** 15/25 tasks (60%)

---

## Completed Phases

### Phase 1: TypeScript Model Deprecations (COMPLETED 2025-10-12)
**Priority:** HIGH | **Actual Effort:** Medium (~4 hours) | **Status:** 6/6 tasks completed

Successfully removed all deprecated TypeScript functions and types from core models:

- Removed deprecated execution helper functions (isExecutionActive, isNodeExecutionActive)
- Updated frontend components to use new isStatusActive() helper
- Deleted deprecated memory.ts file completely
- Removed deprecated IntegrationProvider type
- Rebuilt TypeScript models with no errors
- Regenerated and validated Python code from updated models

**Impact:** Cleaner TypeScript model layer with modern execution status helpers.

### Phase 2: Python Backend Deprecations (COMPLETED 2025-10-12)
**Priority:** HIGH | **Actual Effort:** Medium (~3 hours) | **Status:** 5/5 tasks completed

Successfully removed all deprecated functions and methods from Python backend:

- Removed 6 deprecated AST extraction functions from utils.py
- Removed deprecated get_service() method from ExecutionRequest
- Verified API context already using new service methods (no changes needed)
- Removed deprecated validation helper functions (to_validation_error, to_validation_warning)
- Updated diagram_validator.py to use to_validation_result()
- Removed legacy parse_single_flow() function from flow_parser.py

**Impact:** Cleaner Python backend with modern service lookup patterns and validation methods. Eliminated confusing legacy code paths.

### Phase 3: GraphQL Schema Deprecations (COMPLETED 2025-10-12)
**Priority:** HIGH | **Actual Effort:** Large (~8 hours) | **Status:** 4/4 tasks completed

Successfully removed all deprecated GraphQL fields and migrated frontend to use new data field:

- Migrated frontend hooks to use new `data` field (useApiKeyOperations.ts, useExecution.ts)
- Removed 5 deprecated GraphQL fields from Result types (diagram, node, execution, person, api_key)
- Removed `_DEPRECATED_FIELD_MAP` and backward compatibility logic from strawberry_results.j2 template
- Regenerated GraphQL schema and frontend types successfully
- Fixed import path for Envelope class in generated code
- All frontend TypeScript checks passing

**Impact:** Cleaner GraphQL schema with modern envelope pattern. Frontend now uses consistent `data` field for all result types. Eliminated deprecated field mapping logic from codegen templates.

---

## Active Tasks

### Phase 4: Infrastructure Cleanup
**Priority:** MEDIUM | **Estimated Effort:** Medium (4-6 hours)

Clean up infrastructure-level deprecations and warnings.

#### Task 4.1: Remove deprecated type_definition warning filter
- [ ] Investigate `_type_definition is deprecated` warning filter in /home/soryhyun/DiPeO/apps/server/main.py:56
- [ ] Determine if the underlying issue has been resolved
- [ ] Remove warning filter if safe, or update to proper fix
- [ ] Test server startup for any warnings
- Estimated effort: Medium (2 hours)

#### Task 4.2: Update infrastructure documentation
- [ ] Update /home/soryhyun/DiPeO/docs/architecture/infrastructure-layer.md:54 to remove deprecated database/ directory reference
- [ ] Verify documentation reflects current infrastructure structure
- [ ] Update any other outdated infrastructure references
- Estimated effort: Small (1 hour)

#### Task 4.3: Plan migration for legacy TypeScript type mappings
- [ ] Review /home/soryhyun/DiPeO/apps/web/src/infrastructure/types/fieldTypeRegistry.ts for legacy mappings
- [ ] Create migration plan for modernizing type mappings
- [ ] Document recommended approach for future updates
- Estimated effort: Medium (2 hours)

---

### Phase 5: Documentation Updates
**Priority:** MEDIUM | **Estimated Effort:** Small (2-3 hours)

Update documentation to remove deprecation notices.

#### Task 5.1: Update codegen documentation
- [ ] Update /home/soryhyun/DiPeO/dipeo/infrastructure/codegen/AGENTS.md:35-38 to remove "to be deprecated" notes about legacy IR builders
- [ ] Clarify current state of IR builders
- [ ] Update any related documentation
- Estimated effort: Small (1 hour)

#### Task 5.2: Review code generation guide
- [ ] Review /home/soryhyun/DiPeO/docs/projects/code-generation-guide.md for deprecation references
- [ ] Update if needed to reflect removal of deprecated code
- [ ] Ensure guide reflects current best practices
- Estimated effort: Small (1 hour)

---

### Phase 6: NPM Package Deprecations (Optional/Low Priority)
**Priority:** LOW | **Estimated Effort:** Medium (4-8 hours)

Review and update deprecated NPM packages.

#### Task 6.1: Review deprecated Babel plugins
- [ ] Audit deprecated Babel plugins in package.json
- [ ] Determine if they are actively used
- [ ] Upgrade or remove if necessary
- Estimated effort: Medium (2-4 hours)

#### Task 6.2: Update deprecated npm packages
- [ ] Review deprecated npm packages: glob, inflight, domexception
- [ ] Consider upgrading to recommended alternatives
- [ ] Test that upgrades don't break existing functionality
- Estimated effort: Medium (2-4 hours)

**Note:** This phase is optional and can be deferred based on priority.

---

### Phase 7: Testing & Validation
**Priority:** CRITICAL | **Estimated Effort:** Large (6-10 hours)

Comprehensive testing after all deprecation removals.

#### Task 7.1: Code generation validation
- [ ] Run `make codegen` after each phase
- [ ] Verify generated code is correct
- [ ] Check for any codegen errors or warnings
- Estimated effort: Medium (2 hours)

#### Task 7.2: Frontend validation
- [ ] Run `pnpm typecheck` for TypeScript validation
- [ ] Run `make lint-web` for frontend linting
- [ ] Test frontend functionality manually
- [ ] Verify GraphQL queries work correctly
- Estimated effort: Large (3 hours)

#### Task 7.3: Backend validation
- [ ] Run `make lint-server` for backend validation
- [ ] Run Python type checking if available
- [ ] Test API endpoints manually
- [ ] Verify diagram execution works
- Estimated effort: Large (3 hours)

#### Task 7.4: Integration testing
- [ ] Run `dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=40`
- [ ] Test other example diagrams
- [ ] Verify CLI commands work
- [ ] Check logs for any deprecation warnings
- Estimated effort: Medium (2 hours)

---

## Progress Summary

**Overall:** 15/25 tasks complete (60%)

**By Phase:**
- Phase 1 (TypeScript Models): 6/6 (100%) - COMPLETED
- Phase 2 (Python Backend): 5/5 (100%) - COMPLETED
- Phase 3 (GraphQL Schema): 4/4 (100%) - COMPLETED
- Phase 4 (Infrastructure): 0/3 (0%) - Not started
- Phase 5 (Documentation): 0/2 (0%) - Not started
- Phase 6 (NPM Packages - Optional): 0/2 (0%) - Not started
- Phase 7 (Testing & Validation): 0/4 (0%) - Not started

**Priority Breakdown:**
- CRITICAL: 4 tasks (Phase 7 - Testing) - RECOMMENDED NEXT
- HIGH: 15 tasks completed (Phases 1-3) - ALL COMPLETED
- MEDIUM: 5 tasks (Phases 4-5)
- LOW: 2 tasks (Phase 6 - Optional)

**Estimated Remaining Effort:**
- Required phases (4-5, 7): 12-21 hours (1.5-3 days full-time)
- Optional phase (6): 4-8 hours additional
- **Total remaining with optional:** 16-29 hours (2-4 days full-time)

---

## Recommended Execution Order

1. ~~**Phase 1 (TypeScript Models)**~~ - COMPLETED
2. ~~**Phase 2 (Python Backend)**~~ - COMPLETED
3. ~~**Phase 3 (GraphQL Schema)**~~ - COMPLETED
4. **Phase 7 (Testing & Validation)** - RECOMMENDED NEXT - All HIGH-priority phases complete
5. **Then Phase 4 (Infrastructure)** - Cleanup
6. **Then Phase 5 (Documentation)** - Update docs
7. **Finally Phase 6 (NPM)** - Optional, low priority

**Important:** All HIGH-priority deprecation removals are complete (Phases 1-3). Running Phase 7 (Testing & Validation) is now critical to ensure all changes work correctly before proceeding with infrastructure cleanup.

---

## Success Metrics

**Quantitative:**
- All 23 required tasks completed (25 if including optional Phase 6)
- Zero deprecation warnings in codebase
- All tests passing (TypeScript + Python)
- GraphQL schema fully updated
- Documentation reflects current state

**Qualitative:**
- Cleaner, more maintainable codebase
- No confusing deprecated code paths
- Clear, modern APIs throughout
- Improved developer experience
- Better code discoverability

---

## Notes

- **Status:** Phases 1-3 completed successfully, Phase 7 (Testing) recommended next
- **Created:** 2025-10-12
- **Phase 1 Completed:** 2025-10-12
- **Phase 2 Completed:** 2025-10-12
- **Phase 3 Completed:** 2025-10-12
- **Risk level:** Medium - Changes span multiple layers (TypeScript, Python, GraphQL, infrastructure)
- **Backward Compatibility:** Some breaking changes expected, coordinate with team
- **Testing Strategy:** Incremental validation after each phase

**Important:** All HIGH-priority deprecation removals are complete (Phases 1-3). Phase 7 (Testing & Validation) should be run next before proceeding with infrastructure cleanup. Phase 6 (NPM packages) is optional and can be deferred.

**Phase 1 Achievements:**
- Removed all deprecated TypeScript execution helpers
- Updated frontend to use modern status helpers
- Cleaned up deprecated types and enums
- Successfully regenerated and validated Python code
- Zero build errors or TypeScript errors

**Phase 2 Achievements:**
- Removed 6 deprecated AST extraction functions
- Removed deprecated get_service() method
- Removed deprecated validation helper functions
- Removed legacy flow parser function
- Backend now uses modern service lookup and validation patterns
- Zero linting errors or runtime issues

**Phase 3 Achievements:**
- Migrated frontend to use new `data` field for all result types
- Removed 5 deprecated GraphQL fields (diagram, node, execution, person, api_key)
- Removed `_DEPRECATED_FIELD_MAP` and backward compatibility logic
- Successfully regenerated GraphQL schema and frontend types
- Fixed Envelope class import path in generated code
- All TypeScript checks passing

---

**Last updated:** 2025-10-12
**Next review:** After Phase 7 completion
