# DiPeO Project Todos

Last updated: 2025-10-11

## Overview

Refactoring `dipeo/domain/diagram/` for better maintainability, consistency, and architectural clarity.

**Current Status:**
- Phase 1 (Foundation): COMPLETE (4/4 tasks)
- Phase 2 (Structural): COMPLETE (4/4 tasks)
- Phase 3 (Polish): IN PROGRESS (3/7 tasks complete)
- Phase 4 (Future): Not started (0/6 tasks)

**Recent Achievement:**
- Phases 1 & 2 eliminated ~571 lines of code and removed 5 deprecated modules
- Introduced configuration-driven design patterns (HandleSpec, FIELD_MAPPINGS)
- Extracted compilation into 6-phase pipeline
- Standardized strategy patterns across formats

**Focus Areas:**
- Validation architecture consolidation
- Person-related logic unification
- Utility module reorganization
- Port interface cleanup

---

## Active Tasks

### Phase 3: Polish & Consistency

#### Task 12: Reorganize Utility Module Structure (Issue #21)
**Priority:** HIGH (elevated from Low) | **Effort:** Medium (3-4 hours)

The utils module has 12 files with unclear boundaries and organization.

**Problem:**
- 12 utility files, some very small (1-2 functions)
- Unclear organization and boundaries
- No logical grouping

**Actions:**
- [ ] Review all files in `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/`
- [ ] Create organized subdirectory structure:
  ```
  utils/
    core/
      handle_operations.py  # Handle ID operations
      node_operations.py    # Node-related utilities
      arrow_operations.py   # Arrow-related utilities
    conversion/
      format_converters.py  # Format conversion utilities
      data_extractors.py    # Data extraction utilities
    graph/
      graph_utils.py        # Graph traversal utilities
    __init__.py             # Clean public API
  ```
- [ ] Move files into organized structure
- [ ] Update all imports across the codebase
- [ ] Create clean public API in `utils/__init__.py`
- [ ] Add module docstrings explaining organization
- [ ] Run tests: `make lint-server`
- [ ] Verify no import errors

**Files affected:**
- All files in `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/`
- Many import statements across diagram module

---

#### Task 24: Consolidate Validation Architecture
**Priority:** HIGH | **Effort:** Medium (4-5 hours)

Multiple validation entry points with unclear boundaries between structural and business validation.

**Problem:**
- `validation/service.py`: Thin wrappers around compiler
- `validation/diagram_validator.py`: BaseValidator with business logic (person/API key validation lines 43-63)
- `validation/utils.py`: Shared utilities for phases
- `compilation/phases/validation_phase.py`: Structural validation
- `ports.py`: DiagramStorageSerializer has validate() method (lines 54-59)

**Actions:**
- [ ] Clarify separation between structural validation (compiler phases) vs. business validation (domain rules)
- [ ] Decide if DiagramValidator should remain or if all validation should go through compiler
- [ ] Move person/API key validation to appropriate location (domain service or separate validator)
- [ ] Consider if validation/service.py thin wrappers add value or should be removed
- [ ] Update validation/README.md to document clear validation architecture
- [ ] Remove validate() method from DiagramStorageSerializer in ports.py (lines 54-59) if redundant
- [ ] Run tests: `make lint-server`

**Files to review:**
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/validation/service.py`
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/validation/diagram_validator.py`
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/validation/utils.py`
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/phases/validation_phase.py`
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/ports.py`

---

#### Task 25: Unify Person-Related Logic
**Priority:** MEDIUM | **Effort:** Small (2-3 hours)

Person logic scattered across multiple modules without clear organization.

**Problem:**
- `person_extractor.py` in utils
- `person_resolver.py` in utils
- Person validation in `diagram_validator.py` (lines 43-54, 56-63)
- Person handling in compilation phases

**Actions:**
- [ ] Review all person-related operations across diagram module
- [ ] Consider creating `utils/person/` subdirectory or single `person_operations.py`
- [ ] Consolidate person extraction, resolution, and validation logic
- [ ] Create clear API boundaries for person-related operations
- [ ] Move person validation from diagram_validator.py to appropriate location
- [ ] Update imports across codebase
- [ ] Run tests: `make lint-server`

**Files to review:**
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/person_extractor.py`
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/person_resolver.py`
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/validation/diagram_validator.py`

---

#### Task 26: Review Port Interface Consistency
**Priority:** LOW | **Effort:** Small (1-2 hours)

Port interfaces mixing concerns - unclear if validate() belongs in serializer.

**Problem:**
- `DiagramStorageSerializer` has validate() method (ports.py:54-59)
- Unclear if this should be in validation module instead
- Potential violation of single responsibility principle

**Actions:**
- [ ] Review all port interfaces in ports.py and segregated_ports.py
- [ ] Ensure each port follows single responsibility principle
- [ ] Move validate() method to appropriate location or document why it belongs in serializer
- [ ] Update documentation for port architecture
- [ ] Run tests: `make lint-server`

**Files to review:**
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/ports.py`
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/segregated_ports.py`

---

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

### Phase 3: Polish & Consistency (Partially Complete)

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

**Results:** Standardized patterns, comprehensive documentation, reduced technical debt

---

## Progress Summary

**Overall:** 11/17 tasks complete (65%)

**By Phase:**
- Phase 1 (Foundation): 4/4 (100%) ✓ COMPLETE
- Phase 2 (Structural): 4/4 (100%) ✓ COMPLETE
- Phase 3 (Polish): 3/7 (43%) - IN PROGRESS
- Phase 4 (Future): 0/6 (0%) - Not started

**Remaining Effort:** ~1-1.5 weeks (part-time)

**Code Reduction:** ~571 lines eliminated + 5 deprecated modules removed

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
- Complete 17 total tasks (11 done, 6 remaining)
- Phases 1 & 2: ~571 lines eliminated ✓
- Configuration-driven design for handles and field mapping ✓
- 6-phase modular compiler ✓
- Standardized strategy patterns ✓
- All linting/type checks pass ✓

**Qualitative:**
- Clearer module boundaries ✓
- Easier to add new node types ✓ (configuration-driven)
- Easier to add new format strategies ✓ (standardized pattern)
- Better test coverage (in progress)
- More maintainable codebase ✓
- Consistent patterns ✓

---

## Notes

- **Current focus:** Phase 3 architectural polish (Tasks 12, 24, 25, 26)
- **Based on:** Comprehensive codebase audit (2025-10-11)
- **Audit scope:** 54 Python files in `dipeo/domain/diagram/`
- **Risk level:** Low (critical work complete)
- **ROI:** High (faster development, fewer bugs, easier onboarding)

**Important:** Tasks are independent and can be worked on incrementally. Each completed task provides immediate value. Prioritize based on current development needs.
