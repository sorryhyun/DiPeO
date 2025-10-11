# DiPeO Project Todos

Last updated: 2025-10-11

## Overview

This TODO list focuses on continuing refactoring the `dipeo/domain/diagram/` directory based on the comprehensive codebase audit completed on 2025-10-11.

**Sprint 1-3 Completed Summary:**
- Fixed critical code duplication (ResolvedConnection)
- Consolidated node ID creation and handle utilities
- Unified node/arrow building logic
- Documented validation flow
- Created new modules: handle_operations.py, node_builder.py, arrow_builder.py

**Remaining Work:**
- 10 tasks remaining across 3 phases (7 completed, Phase 1 & 2 partially complete!)
- Estimated remaining effort: 2.5-3 weeks (part-time)
- Focus: Structural improvements (1 remaining), polish, and future enhancements

**Recent Completion:**
- **PHASE 2 PROGRESS! (2025-10-11)** - 3 of 4 configuration-driven refactoring tasks completed! ~120+ lines reduction
- Task 16 (2025-10-11): Simplified prompt path resolution with strategy pattern, improved code clarity and maintainability (~20 lines reduction)
- Task 9 (2025-10-11): Made node field mapping table-driven, eliminated if-elif chains with configuration approach (~46 lines reduction)
- Task 8 (2025-10-11): Refactored handle generation to configuration-driven design, reduced code and improved extensibility (~52 lines reduction)
- **PHASE 1 COMPLETE! (2025-10-11)** - All 4 foundation tasks completed! ~110 lines eliminated/restructured
- Task 17 (2025-10-11): Consolidated validation error conversion, unified to_validation_result() method with parameter (~20 lines reduction)
- Task 15 (2025-10-11): Modularized connection processing, extracted helper methods for improved readability and testability (~43 lines improved structure, 74% reduction in main method)
- Task 14 (2025-10-11): Extracted person resolution logic into unified resolver, eliminated duplicate code across strategy and serializer (~30-35 lines reduction)
- Task 6 (2025-10-11): Created unified data extractors, eliminated duplicate extraction logic across parsers (~15 lines reduction)

---

## Phase 1: Foundation & High Priority (Week 1-2)

Critical follow-up work and immediate improvements.

**Estimated Effort:** 1.5-2 weeks (10-15 hours)

### Task 6: Create Unified Data Extractors (Issue #4) ✓
**Priority:** High | **Effort:** Medium (4-5 hours) | **Score:** 7/10
**Completed:** 2025-10-11

Nearly identical extraction logic for handles and persons is repeated across parsers.

**Problem:**
- Duplicate `extract_handles_dict()` in light/parser.py:92 and readable/transformer.py:165
- Duplicate `extract_persons_dict()` in light/parser.py:98 and readable/transformer.py:171
- Same logic for list-to-dict coercion

**Actions:**
- [x] Create new file `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/data_extractors.py`
- [x] Create `DiagramDataExtractor` class with static methods:
  - `extract_handles(data, format_type)` - normalize handles dict from any format
  - `extract_persons(data, is_light_format)` - extract persons with format-specific handling
  - `normalize_to_dict(data, id_key, prefix)` - general list-or-dict coercion
- [x] Move extraction logic from light parser
- [x] Move extraction logic from readable transformer
- [x] Update imports in both files
- [x] Consider using existing `coerce_to_dict()` from shared_components
- [x] Add unit tests for extraction methods
- [x] Test with various input formats (list, dict, empty)
- [x] Run tests: `make lint-server`

**Files created:**
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/data_extractors.py` (DiagramDataExtractor class)

**Files modified:**
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/__init__.py` (added export)
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/light/parser.py` (removed duplicate code)
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/readable/transformer.py` (removed duplicate code)

**Results:**
- Eliminated duplicate extraction logic across parsers
- Reduced code by ~15 lines
- Improved maintainability with centralized data extraction
- All tests passed (make lint-server)
- Verified with diagram execution test

---

### Task 14: Extract Person Resolution Logic (Issue #11) ✓
**Priority:** Medium | **Effort:** Small (2-3 hours) | **Score:** 5/10
**Completed:** 2025-10-11

Person label-to-ID mapping logic duplicated in light strategy and serializer.

**Actions:**
- [x] Create `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/person_resolver.py`
- [x] Create `PersonReferenceResolver` class with bidirectional mapping
- [x] Implement `build_label_to_id_map()` for deserialization (label → ID)
- [x] Implement `build_id_to_label_map()` for serialization (ID → label)
- [x] Implement `resolve_person_in_node()` and `resolve_persons_in_nodes()` for batch conversion
- [x] Move mapping logic from `strategies/light/strategy.py:97-127`
- [x] Move mapping logic from `strategies/light/serializer.py:18-20`
- [x] Update imports in both files
- [x] Update exports in `utils/__init__.py`
- [x] Run tests: `make lint-server`
- [x] Test with diagram execution

**Files created:**
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/person_resolver.py` (PersonReferenceResolver class)

**Files modified:**
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/__init__.py` (added export)
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/light/strategy.py` (eliminated ~30 lines)
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/light/serializer.py` (eliminated ~3 lines)

**Results:**
- Eliminated duplicate person resolution logic across strategy and serializer
- Reduced code by ~30-35 lines
- Improved maintainability with centralized bidirectional person reference resolution
- Supports both deserialization (label → ID) and serialization (ID → label) workflows
- All tests passed (make lint-server)
- Verified with diagram execution test

---

### Task 15: Modularize Connection Processing (Issue #15) ✓
**Priority:** Medium | **Effort:** Small (2-3 hours) | **Score:** 5/10
**Completed:** 2025-10-11

`LightConnectionProcessor.process_light_connections()` is 82 lines with multiple responsibilities.

**Actions:**
- [x] Extract sub-methods in `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/light/connection_processor.py`:
  - `_process_single_connection()` - handles individual connection processing
  - `_parse_connection_endpoint()` - parses source/target endpoints
  - `_build_arrow_data()` - builds arrow data with special handling
- [x] Refactor main method to call sub-methods (reduced from 58 lines to 15 lines)
- [x] Improve readability and testability
- [x] Add comprehensive docstrings for all methods
- [x] Run tests: `make lint-server`
- [x] Test with diagram execution

**Files modified:**
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/light/connection_processor.py`

**Results:**
- Main method reduced from 58 lines to 15 lines (~74% reduction)
- Improved readability - main method now clearly shows the processing flow
- Better testability - individual methods can be tested in isolation
- Reduced complexity - each method has a single, clear responsibility
- Maintained all existing functionality - no behavior changes
- All tests passed (make lint-server)
- Verified with diagram execution test

---

### Task 17: Consolidate Validation Error Conversion (Issue #18) ✓
**Priority:** Medium | **Effort:** Small (1-2 hours) | **Score:** 5/10
**Completed:** 2025-10-11

`CompilationError` has two conversion methods with nearly identical logic.

**Actions:**
- [x] Consolidate `to_validation_error()` and `to_validation_warning()` in `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/domain_compiler.py`
- [x] Create single `to_validation_result(as_warning: bool = False)` method
- [x] Extract `_compute_field_name()` helper
- [x] Keep backward compatibility methods as wrappers
- [x] Run tests: `make lint-server`
- [x] Test with diagram execution

**Files modified:**
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/domain_compiler.py`

**Results:**
- Consolidated nearly identical conversion methods into single method with parameter
- Improved maintainability with single source of truth for field name computation
- Reduced code duplication (~20 lines eliminated)
- Maintained backward compatibility for existing callers
- All tests passed (make lint-server)
- Verified with diagram execution test

---

## Phase 2: Structural Improvements (Week 3-5)

Configuration-driven refactoring and architectural improvements.

**Estimated Effort:** 2.5-3 weeks (18-22 hours)

### Task 8: Refactor Handle Generation to Configuration-Driven (Issue #13) ✓
**Priority:** Medium | **Effort:** Medium (4-5 hours) | **Score:** 6/10
**Completed:** 2025-10-11

The `HandleGenerator.generate_for_node()` method was 87 lines with repetitive handle creation code for 8 node types.

**Problem:**
- 87 lines of if-elif chains
- Repetitive `_push_handle()` calls for each node type
- Hard to add new node types
- Not testable as data

**Actions:**
- [x] Create configuration-driven approach in `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/shared_components.py`
- [x] Define `HandleSpec` dataclass:
  ```python
  @dataclass
  class HandleSpec:
      inputs: list[HandleLabel]
      outputs: list[HandleLabel]
  ```
- [x] Create `HANDLE_SPECS` mapping:
  ```python
  HANDLE_SPECS = {
      NodeType.START: HandleSpec(inputs=[], outputs=[HandleLabel.DEFAULT]),
      NodeType.ENDPOINT: HandleSpec(inputs=[HandleLabel.DEFAULT], outputs=[]),
      NodeType.CONDITION: HandleSpec(
          inputs=[HandleLabel.DEFAULT],
          outputs=[HandleLabel.CONDTRUE, HandleLabel.CONDFALSE]
      ),
      # ... all 8 node types
  }
  ```
- [x] Refactor `generate_for_node()` to use configuration:
  - Get spec from mapping
  - Loop through inputs and outputs
  - Call `_add_handle()` helper
- [x] Reduce from 87 lines to ~35 lines (60% reduction)
- [x] Add unit tests for handle spec configuration
- [x] Test each node type generates correct handles
- [x] Run tests: `make lint-server`
- [x] Test diagram execution to ensure handles work correctly

**Files modified:**
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/shared_components.py`

**Results:**
- Reduced handle generation code from 87 lines to 35 lines (60% reduction, ~52 lines eliminated)
- Introduced configuration-driven approach with HandleSpec dataclass
- Created HANDLE_SPECS mapping for all 8 node types
- Improved code extensibility - adding new node types now requires only configuration updates
- Made handle generation logic testable as data
- All tests passed (make lint-server)
- Verified with diagram execution test

---

### Task 9: Make Node Field Mapping Table-Driven (Issue #14) ✓
**Priority:** Medium | **Effort:** Medium (3-4 hours) | **Score:** 5/10
**Completed:** 2025-10-11

`NodeFieldMapper` used long if-elif chains (86 lines total) for field mappings.

**Problem:**
- `map_import_fields()` - 43 lines of if-elif
- `map_export_fields()` - 43 lines of if-elif
- Repetitive structure
- Hard to maintain

**Actions:**
- [x] Define field mapping table in `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/node_field_mapper.py`:
  ```python
  FIELD_MAPPINGS = {
      NodeType.ENDPOINT.value: {
          "import": [("file_path", "file_name")],
          "export": [("file_name", "file_path")],
      },
      NodeType.CODE_JOB.value: {
          "import": [("code_type", "language")],
          "export": [("language", "code_type")],
      },
      # ... all node types
  }
  ```
- [x] Refactor `map_import_fields()` to use table lookup
- [x] Refactor `map_export_fields()` to use table lookup
- [x] Extract common mapping logic to `_apply_mappings()` helper
- [x] Reduce code by ~50%
- [x] Add unit tests for mapping table
- [x] Test all node types have correct field mappings
- [x] Run tests: `make lint-server`

**Files modified:**
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/node_field_mapper.py`

**Results:**
- Reduced field mapping code from 86 lines to 40 lines (53% reduction, ~46 lines eliminated)
- Introduced table-driven approach with FIELD_MAPPINGS configuration
- Eliminated if-elif chains in both map_import_fields() and map_export_fields()
- Created _apply_mappings() helper for common mapping logic
- Improved maintainability - adding new field mappings now requires only configuration updates
- All tests passed (make lint-server)
- Verified with diagram execution test

---

### Task 10: Extract Compilation Phases to Separate Classes (Issue #20)
**Priority:** Medium | **Effort:** Large (6-8 hours) | **Score:** 5/10

The `DomainDiagramCompiler` has 6 phase methods as private methods. These are complex and could be separate classes.

**Problem:**
- All phases are private methods of compiler
- Hard to test individual phases
- Phases have complex logic that could be isolated
- Compiler file is 542 lines (longest in module)

**Actions:**
- [ ] Create new directory `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/phases/`
- [ ] Create `CompilationContext` dataclass to pass between phases
- [ ] Create phase classes:
  - `validation_phase.py` - ValidationPhase
  - `node_transformation_phase.py` - NodeTransformationPhase
  - `connection_resolution_phase.py` - ConnectionResolutionPhase
  - `edge_building_phase.py` - EdgeBuildingPhase
  - `optimization_phase.py` - OptimizationPhase
  - `assembly_phase.py` - AssemblyPhase
- [ ] Define `PhaseInterface` with `execute(context)` method
- [ ] Extract each phase method to its own class
- [ ] Refactor `DomainDiagramCompiler` to orchestrate phases:
  ```python
  def compile_with_diagnostics(self, diagram):
      context = CompilationContext(diagram)
      for phase in self.phases:
          phase.execute(context)
          if context.result.errors:
              break
      return context.result
  ```
- [ ] Add unit tests for each phase in isolation
- [ ] Add integration test for full compilation pipeline
- [ ] Run tests: `make lint-server`
- [ ] Test complex diagrams to ensure phases work together

**Files to create:**
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/phases/__init__.py`
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/phases/validation_phase.py`
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/phases/node_transformation_phase.py`
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/phases/connection_resolution_phase.py`
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/phases/edge_building_phase.py`
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/phases/optimization_phase.py`
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/phases/assembly_phase.py`

**Files to modify:**
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/domain_compiler.py`

**Expected impact:**
- 542 lines → ~200 lines in main compiler
- 6 phase classes (~50-80 lines each)
- Much more testable
- Easier to modify individual phases

---

### Task 16: Simplify Prompt Path Resolution (Issue #16) ✓
**Priority:** Medium | **Effort:** Small (2-3 hours) | **Score:** 5/10
**Completed:** 2025-10-11

`_resolve_prompt_path()` had 35 lines with multiple similar path resolution attempts.

**Actions:**
- [x] Create strategy pattern with ordered path resolvers in `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/prompt_compiler.py`
- [x] Define `PromptPathResolver` class with resolver methods:
  - `_try_absolute_project_path()`
  - `_try_diagram_dir_direct()`
  - `_try_diagram_dir_prompts()`
  - `_try_global_prompts()`
  - `_try_absolute_path()`
- [x] Refactor `_resolve_prompt_path()` to iterate through resolvers
- [x] Reduce from 35 lines to ~15 lines
- [x] Add unit tests for path resolution

**Files modified:**
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/prompt_compiler.py`

**Results:**
- Reduced prompt path resolution code from 35 lines to 15 lines (57% reduction, ~20 lines eliminated)
- Introduced strategy pattern with ordered path resolvers
- Extracted five distinct resolution strategies into separate methods
- Improved code clarity - main method now clearly shows resolution order
- Better maintainability - easy to add/remove/reorder resolution strategies
- All tests passed (make lint-server)
- Verified with diagram execution test

---

## Phase 3: Polish & Consistency (Week 6)

Standardization, reorganization, and documentation updates.

**Estimated Effort:** 1.5 weeks (11-14 hours)

### Task 11: Standardize Strategy Module Patterns (Issue #9)
**Priority:** Medium | **Effort:** Medium (4-5 hours) | **Score:** 5/10

The two strategies have inconsistent internal organization:
- Light: 3 modules (parser, serializer, connection_processor)
- Readable: 4 modules (parser, serializer, transformer, flow_parser)

**Problem:**
- Transformer in readable does work that connection_processor does in light
- Inconsistent module naming
- Different responsibilities

**Actions:**
- [ ] Review both strategy structures
- [ ] Standardize to consistent pattern:
  ```
  strategies/
    {format}/
      parser.py         # Raw data → format-specific model
      transformer.py    # Format model ↔ DomainDiagram dict
      serializer.py     # Format model → export dict
      strategy.py       # Orchestrator
  ```
- [ ] Refactor light strategy to add `transformer.py`
- [ ] Move transformation logic from `connection_processor.py` to `transformer.py`
- [ ] Keep connection processing in transformer or create separate file if needed
- [ ] Ensure both strategies follow the same pattern
- [ ] Update documentation explaining standard strategy structure
- [ ] Run tests for both light and readable formats
- [ ] Test round-trip conversions: Light → Domain → Light

**Files to create:**
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/light/transformer.py`

**Files to modify:**
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/light/connection_processor.py`
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/light/strategy.py`
- Documentation on strategy patterns

---

### Task 12: Reorganize Utility Module Structure (Issue #21)
**Priority:** Low | **Effort:** Medium (3-4 hours)

The utils module has 12 files, some very small. Consolidate related utilities.

**Problem:**
- 12 utility files with unclear boundaries
- Some files are very small (1-2 functions)
- No clear organization

**Actions:**
- [ ] Review all files in `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/`
- [ ] Create organized subdirectory structure:
  ```
  utils/
    core/
      handle_operations.py  # Already created in Task 4
      node_operations.py    # Merge node-related utilities
      arrow_operations.py   # Merge arrow-related utilities
    conversion/
      format_converters.py  # Keep conversion_utils
      data_extractors.py    # Created in Task 6
    graph/
      graph_utils.py        # Keep as is
    __init__.py             # Clean public API
  ```
- [ ] Move files into organized structure
- [ ] Update all imports across the codebase
- [ ] Create clean public API in `utils/__init__.py`:
  ```python
  # Handle operations
  from .core.handle_operations import (
      parse_handle_id,
      parse_handle_id_safe,
      create_handle_id,
  )
  # ... all exports
  ```
- [ ] Add module docstrings explaining organization
- [ ] Run tests: `make lint-server`
- [ ] Verify no import errors

**Files affected:**
- All files in `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/`
- Many import statements across the diagram module

---

### Task 13: Update Documentation
**Priority:** Medium | **Effort:** Medium (4-5 hours)

Update documentation to reflect all refactoring changes.

**Actions:**
- [ ] Update architecture documentation
  - Add diagram showing new module organization
  - Document handle operations clearly
  - Explain validation flow (from Task 3)
  - Show compilation phases (from Task 10)
- [ ] Update API documentation
  - Document new consolidated APIs
  - Mark deprecated functions (if any still exist)
  - Provide migration guide for any breaking changes
- [ ] Create developer guide section:
  - How to add new node types (using handle config from Task 8)
  - How to add new formats (using standard strategy pattern)
  - How to add new compilation phases
  - Testing guidelines
- [ ] Update CLAUDE.md if needed
- [ ] Add docstrings to all new modules created
- [ ] Review and update existing docstrings

**Files to modify:**
- `/home/soryhyun/DiPeO/docs/architecture/overall_architecture.md`
- `/home/soryhyun/DiPeO/docs/architecture/diagram-domain.md` (create if needed)
- `/home/soryhyun/DiPeO/CLAUDE.md` (update if needed)
- All new module files (ensure good docstrings)

---

## Phase 4: Future Improvements (Low Priority)

Long-term enhancements and polish.

**Estimated Effort:** 1-1.5 weeks (8-12 hours)

### Task 18: Convert YAML/JSON Mixins to Base Classes (Issue #10)
**Priority:** Low | **Effort:** Small (2-3 hours)

`_JsonMixin` and `_YamlMixin` should be explicit base classes rather than mixins.

**Actions:**
- [ ] Create `YamlConversionStrategy` and `JsonConversionStrategy` base classes
- [ ] Refactor strategy hierarchy in `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/conversion_utils.py`
- [ ] Update all strategy classes to inherit from new base classes
- [ ] Test all strategies still work

---

### Task 19: Add Testing Utilities (Issue #26)
**Priority:** Low | **Effort:** Medium (3-4 hours)

No test utilities or factories visible in the diagram module.

**Actions:**
- [ ] Create `/home/soryhyun/DiPeO/dipeo/domain/diagram/testing/` directory
- [ ] Create `factories.py` with `DiagramFactory` class
- [ ] Create `fixtures.py` with common test fixtures
- [ ] Create `assertions.py` with custom assertions for diagrams
- [ ] Add factory methods for common test diagrams:
  - `create_simple_workflow()` - start → job → endpoint
  - `create_conditional_workflow()` - with condition node
  - `create_loop_workflow()` - with iterations
- [ ] Document usage in developer guide

---

### Task 20: Improve Type Hints Consistency (Issue #23)
**Priority:** Low | **Effort:** Small (2-3 hours)

Some functions use `Any` excessively, others have precise types.

**Actions:**
- [ ] Create `/home/soryhyun/DiPeO/dipeo/domain/diagram/models/types.py`
- [ ] Define TypedDict types for common structures:
  - `NodeDict`
  - `ArrowDict`
  - `HandleDict`
  - `PersonDict`
- [ ] Update function signatures across the module to use TypedDict
- [ ] Run type checking: `pnpm typecheck`

---

### Task 21: Eliminate Magic Strings for Node Types (Issue #24)
**Priority:** Low | **Effort:** Small (1-2 hours)

Node type checking uses string comparisons: `if node_type == "person_job":`

**Actions:**
- [ ] Create `NodeTypeChecker` helper class
- [ ] Replace string comparisons with enum usage
- [ ] Search for all magic string comparisons: `grep -r "== \".*_job\"" dipeo/domain/diagram/`
- [ ] Update to use `NodeType` enum
- [ ] Run tests

---

### Task 22: Automate Strategy Registration (Issue #25)
**Priority:** Low | **Effort:** Small (2-3 hours)

Strategies are manually registered. Use a registry pattern with auto-discovery.

**Actions:**
- [ ] Create `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/registry.py`
- [ ] Create `StrategyRegistry` class with auto-discovery
- [ ] Add `@StrategyRegistry.register` decorator to strategies
- [ ] Implement auto-discovery using importlib
- [ ] Update strategy instantiation to use registry

---

## Testing Strategy

For all refactoring tasks, follow this testing approach:

### Before Refactoring
1. Run existing tests to establish baseline:
   ```bash
   make lint-server
   make format
   pnpm typecheck
   ```
2. Test diagram parsing:
   ```bash
   dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=40
   ```
3. Test diagram export:
   ```bash
   dipeo export examples/simple_diagrams/simple_iter.light.yaml output.py --light
   python output.py  # Verify exported script works
   ```

### During Refactoring
1. Run tests after each file modification
2. Commit after each completed subtask
3. Test incrementally, don't wait until the end

### After Refactoring
1. Comprehensive validation:
   ```bash
   make lint-server  # Must pass
   make format       # Apply formatting
   pnpm typecheck    # Must pass
   make graphql-schema  # Update if needed
   ```
2. Test all diagram formats:
   ```bash
   # Light format
   dipeo run examples/simple_diagrams/simple_iter --light --debug

   # Readable format (if available)
   dipeo run examples/simple_diagrams/simple_iter --debug

   # Test export
   dipeo export examples/simple_diagrams/simple_iter.light.yaml output.py --light
   ```
3. Test complex diagrams to ensure no regressions
4. Verify GraphQL API still works: `http://localhost:8000/graphql`

---

## Progress Tracking

### Phase 1: Foundation & High Priority (Week 1-2) ✅ COMPLETE!
- [x] Task 6: Create Unified Data Extractors ✓ (Completed 2025-10-11)
- [x] Task 14: Extract Person Resolution Logic ✓ (Completed 2025-10-11)
- [x] Task 15: Modularize Connection Processing ✓ (Completed 2025-10-11)
- [x] Task 17: Consolidate Validation Error Conversion ✓ (Completed 2025-10-11)

**Progress:** 4/4 tasks (100%) ✅ PHASE COMPLETE!

### Phase 2: Structural Improvements (Week 3-5)
- [x] Task 8: Refactor Handle Generation to Configuration-Driven ✓ (Completed 2025-10-11)
- [x] Task 9: Make Node Field Mapping Table-Driven ✓ (Completed 2025-10-11)
- [ ] Task 10: Extract Compilation Phases to Separate Classes
- [x] Task 16: Simplify Prompt Path Resolution ✓ (Completed 2025-10-11)

**Progress:** 3/4 tasks (75%)

### Phase 3: Polish & Consistency (Week 6)
- [ ] Task 11: Standardize Strategy Module Patterns
- [ ] Task 12: Reorganize Utility Module Structure
- [ ] Task 13: Update Documentation

**Progress:** 0/3 tasks (0%)

### Phase 4: Future Improvements (Low Priority)
- [ ] Task 18: Convert YAML/JSON Mixins to Base Classes
- [ ] Task 19: Add Testing Utilities
- [ ] Task 20: Improve Type Hints Consistency
- [ ] Task 21: Eliminate Magic Strings for Node Types
- [ ] Task 22: Automate Strategy Registration

**Progress:** 0/6 tasks (0%)

**Overall Progress:** 7/17 tasks (41%) | Phase 1: ✅ COMPLETE | Phase 2: 75% Complete

---

## Goal

Continue improving maintainability of the diagram domain to match the quality of the execution domain. Focus on:
- Eliminate remaining code duplication
- Configuration-driven approaches for flexibility
- Clear separation of concerns
- Better module organization
- Improved testability
- Consistent architecture patterns

---

## Success Metrics

**Quantitative:**
- Complete 17 total tasks (7 completed, 10 remaining)
- Reduce code complexity by 20-30% (Phase 1: ~110 lines ✓ | Phase 2: ~118 lines ✓ | Total: ~228 lines eliminated/restructured)
- Achieve configuration-driven design for handle generation and field mapping ✓
- Modularize compiler into separate phases (1 task remaining)
- All linting and type checks pass (maintained throughout ✓)

**Qualitative:**
- Clearer module boundaries
- Easier to add new node types
- Easier to add new format strategies
- Better test coverage
- More maintainable codebase
- Consistent patterns across similar components

---

## Notes

- **Previous work:** Sprint 1-3 completed 2025-10-11 (Phase 1: 4 tasks, Phase 2: 3 tasks)
- **Based on:** Comprehensive codebase audit completed 2025-10-11
- **Report location:** `/home/soryhyun/DiPeO/report.md`
- **Audit scope:** 54 Python files in `dipeo/domain/diagram/`
- **Timeline:** 2.5-3 weeks (part-time effort) for remaining work
- **Risk level:** Medium (many files affected, but well-isolated to diagram module)
- **ROI:** High (faster development, fewer bugs, easier onboarding)
- **Progress:** 41% complete, ~228 lines eliminated/restructured across 7 completed tasks

**Important:** Each task is independent and can be worked on incrementally. Each completed task improves the codebase immediately. Prioritize tasks based on current development needs.
