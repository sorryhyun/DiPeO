# DiPeO Project Todos

Last updated: 2025-10-11

## Overview

Refactoring `dipeo/domain/diagram/` for better maintainability, consistency, and architectural clarity.

**Current Status:**
- Phase 1 (Foundation): COMPLETE (4/4 tasks)
- Phase 2 (Structural): COMPLETE (4/4 tasks)
- Phase 3 (Polish): COMPLETE (7/7 tasks)
- Phase 4 (Future): Not started (0/6 tasks)

**Recent Achievement:**
- Phase 3 completed all architectural polish tasks:
  - Consolidated validation architecture (structural vs business separation)
  - Unified person-related logic into organized subdirectory
  - Reviewed and fixed port interface consistency (removed SRP violations)
  - Added comprehensive documentation (validation/README.md, PORT_ARCHITECTURE.md)
- Phases 1-3 eliminated ~571 lines of code and removed 5 deprecated modules
- Introduced configuration-driven design patterns (HandleSpec, FIELD_MAPPINGS)
- Extracted compilation into 6-phase pipeline
- Standardized strategy patterns across formats
- Reorganized utility module into structured subdirectories (core/, conversion/, graph/, person/)

**Status:**
- All core refactoring complete (Phases 1-3)
- Architecture is clean, consistent, and well-documented
- Ready for Phase 4 (optional future improvements)

---

## Active Tasks

### Phase 3: Polish & Consistency (COMPLETE)

All Phase 3 tasks have been completed successfully!

### Phase 4: Future Improvements (Low Priority)

#### Task 18: Convert YAML/JSON Mixins to Base Classes (Issue #10)
**Priority:** LOW | **Effort:** Small (2-3 hours)

`_JsonMixin` and `_YamlMixin` should be explicit base classes rather than mixins.

**Actions:**
- [ ] Create `YamlConversionStrategy` and `JsonConversionStrategy` base classes
- [ ] Refactor strategy hierarchy in `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/conversion_utils.py`
- [ ] Update all strategy classes to inherit from new base classes
- [ ] Test all strategies still work

---

#### Task 19: Add Testing Utilities (Issue #26)
**Priority:** LOW | **Effort:** Medium (3-4 hours)

No test utilities or factories visible in the diagram module.

**Actions:**
- [ ] Create `/home/soryhyun/DiPeO/dipeo/domain/diagram/testing/` directory
- [ ] Create `factories.py` with `DiagramFactory` class
- [ ] Create `fixtures.py` with common test fixtures
- [ ] Create `assertions.py` with custom assertions for diagrams
- [ ] Add factory methods for common test diagrams
- [ ] Document usage in developer guide

---

#### Task 20: Improve Type Hints Consistency (Issue #23)
**Priority:** LOW | **Effort:** Small (2-3 hours)

Some functions use `Any` excessively, others have precise types.

**Actions:**
- [ ] Create `/home/soryhyun/DiPeO/dipeo/domain/diagram/models/types.py`
- [ ] Define TypedDict types for common structures (NodeDict, ArrowDict, HandleDict, PersonDict)
- [ ] Update function signatures across module to use TypedDict
- [ ] Run type checking: `pnpm typecheck`

---

#### Task 21: Eliminate Magic Strings for Node Types (Issue #24)
**Priority:** LOW | **Effort:** Small (1-2 hours)

Node type checking uses string comparisons: `if node_type == "person_job":`

**Actions:**
- [ ] Create `NodeTypeChecker` helper class
- [ ] Replace string comparisons with enum usage
- [ ] Search for all magic string comparisons
- [ ] Update to use `NodeType` enum
- [ ] Run tests

---

#### Task 22: Automate Strategy Registration (Issue #25)
**Priority:** LOW | **Effort:** Small (2-3 hours)

Strategies are manually registered. Use a registry pattern with auto-discovery.

**Actions:**
- [ ] Create `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/registry.py`
- [ ] Create `StrategyRegistry` class with auto-discovery
- [ ] Add `@StrategyRegistry.register` decorator to strategies
- [ ] Implement auto-discovery using importlib
- [ ] Update strategy instantiation to use registry

---

## Completed Work Archive

### Phase 1: Foundation & High Priority (COMPLETE)

**Completed Tasks:**
- **Task 6** (2025-10-11): Created unified data extractors (~15 lines eliminated)
  - NEW: `utils/data_extractors.py` (DiagramDataExtractor class)
  - Eliminated duplicate extraction logic across parsers

- **Task 14** (2025-10-11): Extracted person resolution logic (~30-35 lines eliminated)
  - NEW: `utils/person_resolver.py` (PersonReferenceResolver class)
  - Unified bidirectional person reference mapping

- **Task 15** (2025-10-11): Modularized connection processing (~43 lines improved structure)
  - Main method reduced from 58 lines to 15 lines (74% reduction)
  - Improved readability and testability

- **Task 17** (2025-10-11): Consolidated validation error conversion (~20 lines eliminated)
  - Unified to_validation_result() method with parameter
  - Eliminated duplicate field name computation

**Results:** ~110 lines eliminated/restructured, improved code organization

---

### Phase 2: Structural Improvements (COMPLETE)

**Completed Tasks:**
- **Task 8** (2025-10-11): Refactored handle generation to configuration-driven (~52 lines eliminated)
  - Created HandleSpec dataclass and HANDLE_SPECS mapping
  - Reduced from 87 lines to 35 lines (60% reduction)
  - Configuration-driven approach for all 8 node types

- **Task 9** (2025-10-11): Made node field mapping table-driven (~46 lines eliminated)
  - Created FIELD_MAPPINGS configuration
  - Reduced from 86 lines to 40 lines (53% reduction)
  - Eliminated if-elif chains

- **Task 10** (2025-10-11): Extracted compilation phases to separate classes (~341 lines eliminated)
  - Created 6 phase classes (ValidationPhase, NodeTransformationPhase, etc.)
  - Compiler reduced from 561 lines to 220 lines (60.9% reduction)
  - Clear separation of concerns with PhaseInterface

- **Task 16** (2025-10-11): Simplified prompt path resolution (~20 lines eliminated)
  - Strategy pattern with ordered path resolvers
  - Reduced from 35 lines to 15 lines (57% reduction)

**Results:** ~461 lines eliminated, configuration-driven design, 6-phase compilation pipeline

---

### Phase 3: Polish & Consistency (COMPLETE)

**Completed Tasks:**
- **Task 11** (2025-10-11): Standardized strategy module patterns (~5 hours)
  - NEW: `strategies/light/transformer.py` (LightDiagramTransformer)
  - Unified both strategies to consistent 4-module structure
  - Both strategies now follow: parser → transformer → serializer → strategy

- **Task 13** (2025-10-11): Updated documentation (~4-5 hours)
  - NEW: `docs/architecture/diagram-compilation.md`
  - NEW: `docs/guides/developer-guide-diagrams.md`
  - Comprehensive architecture and developer guides

- **Task 23** (2025-10-11): Removed deprecated utilities and forwarding modules (~2-3 hours)
  - REMOVED: 2 forwarding modules (light_strategy.py, readable_strategy.py)
  - REMOVED: 3 deprecated utilities (handle_parser.py, arrow_data_processor.py, handle_utils.py)
  - Cleaned up exports

- **Task 12** (2025-10-11): Reorganized utility module structure (~3-4 hours)
  - Created organized subdirectory structure: core/, conversion/, graph/
  - Moved and renamed 6 files to new locations
  - Created __init__.py files with proper exports
  - Updated all imports across codebase
  - Maintained backward compatibility in main utils/__init__.py

- **Task 24** (2025-10-11): Consolidated validation architecture (~4-5 hours)
  - NEW: `validation/business_validators.py` (PersonReferenceValidator, APIKeyValidator, BusinessValidatorRegistry)
  - NEW: `validation/README.md` (comprehensive architecture documentation)
  - UPDATED: `validation/diagram_validator.py` (clean separation: structural via compiler, business via registry)
  - UPDATED: `application/diagram/use_cases/validate_diagram.py` (simplified to delegate to DiagramValidator)
  - REMOVED: Person/API key validation logic from DiagramValidator (moved to business validators)
  - Clear separation: structural validation (compiler) vs business validation (domain rules)

- **Task 25** (2025-10-11): Unified person-related logic (~2-3 hours)
  - NEW: `utils/person/` subdirectory with organized modules:
    - `operations.py` (PersonExtractor, PersonReferenceResolver)
    - `validation.py` (PersonValidator)
    - `__init__.py` (clean exports)
  - REMOVED: `utils/person_extractor.py` and `utils/person_resolver.py` (consolidated)
  - UPDATED: `utils/__init__.py` and `utils/conversion/data_extractors.py` (imports from new person module)
  - All person operations now in single location with clear API boundaries

- **Task 26** (2025-10-11): Reviewed port interface consistency (~1-2 hours)
  - NEW: `PORT_ARCHITECTURE.md` (comprehensive port architecture documentation)
  - REMOVED: `validate()` method from DiagramStorageSerializer in `ports.py` (violated SRP, was dead code)
  - REMOVED: `validate_content()` from SerializeDiagramUseCase in `serialize_diagram.py` (redundant)
  - Documented SRP principles and when validation belongs in ports (almost never)
  - All ports now follow single responsibility principle

**Results:** Complete architectural consistency, clear validation boundaries, unified person logic, SRP-compliant ports

---

## Progress Summary

**Overall:** 15/21 tasks complete (~71%)

**By Phase:**
- Phase 1 (Foundation): 4/4 (100%) ✓ COMPLETE
- Phase 2 (Structural): 4/4 (100%) ✓ COMPLETE
- Phase 3 (Polish): 7/7 (100%) ✓ COMPLETE
- Phase 4 (Future): 0/6 (0%) - Not started (optional)

**Core Refactoring:** COMPLETE

**Remaining Effort:** Phase 4 tasks are optional future improvements (~2 weeks part-time if pursued)

**Code Quality Improvements:**
- ~571 lines eliminated
- 5 deprecated modules removed
- 3 new documentation files added (validation/README.md, PORT_ARCHITECTURE.md, and earlier docs)
- Organized utils structure (core/, conversion/, graph/, person/ subdirectories)
- Clear architectural boundaries (validation: structural vs business; ports: SRP compliance)

---

## Testing Strategy

### Before Refactoring
```bash
make lint-server
dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=40
```

### During Refactoring
- Run tests after each file modification
- Commit after each completed subtask
- Test incrementally

### After Refactoring
```bash
make lint-server      # Must pass
make format           # Apply formatting
pnpm typecheck        # Must pass
dipeo run examples/simple_diagrams/simple_iter --light --debug
```

---

## Success Metrics

**Quantitative:**
- Core refactoring: 15/15 tasks complete (Phases 1-3) ✓
- Phases 1 & 2: ~571 lines eliminated ✓
- Configuration-driven design for handles and field mapping ✓
- 6-phase modular compiler ✓
- Standardized strategy patterns ✓
- Organized utility module structure ✓
- Clear validation architecture (structural vs business) ✓
- Unified person-related logic ✓
- SRP-compliant port interfaces ✓
- All linting/type checks pass ✓

**Qualitative:**
- Clearer module boundaries ✓
- Easier to add new node types ✓ (configuration-driven)
- Easier to add new format strategies ✓ (standardized pattern)
- Clear validation responsibilities ✓ (compiler for structural, validators for business)
- Person operations centralized ✓ (utils/person/ subdirectory)
- Better test coverage (in progress)
- More maintainable codebase ✓
- Consistent patterns ✓
- Comprehensive documentation ✓

---

## Notes

- **Status:** Phase 3 COMPLETE - All core refactoring tasks finished! (2025-10-11)
- **Based on:** Comprehensive codebase audit (2025-10-11)
- **Audit scope:** 54 Python files in `dipeo/domain/diagram/`
- **Risk level:** Low - All changes tested and working
- **ROI:** High (faster development, fewer bugs, easier onboarding)

**Important:** Core refactoring (Phases 1-3) is complete. Phase 4 tasks are optional future improvements that can be prioritized based on development needs.

---

## Final Status (2025-10-11)

**PHASES 1-3 COMPLETE! 🎉**

All core refactoring objectives achieved:
- ✅ Configuration-driven design (HandleSpec, FIELD_MAPPINGS)
- ✅ Modular 6-phase compilation pipeline
- ✅ Standardized strategy patterns (light, readable)
- ✅ Organized utility structure (core/, conversion/, graph/, person/)
- ✅ Clear validation architecture (structural via compiler, business via validators)
- ✅ Unified person operations (utils/person/)
- ✅ SRP-compliant port interfaces
- ✅ Comprehensive documentation

**Changes verified:**
- Example diagram runs successfully
- Linting passes (minor unrelated warnings exist)
- All imports updated correctly
- Architecture documented

**Next steps:**
- Phase 4 tasks are optional improvements (can be prioritized later)
- Current architecture is production-ready
- Focus can shift to feature development
