# DiPeO TODO

## Current Priority: Refactor `/dipeo/application/execution/`

### Current State (CORRECTED)
- **13,665 lines** across 63 files (previous count was wrong)
- **Largest file:** 603 lines (person_job/__init__.py)
- **Major issues:** Code duplication (~800 lines), missing abstractions, mixed concerns
- **Missing subsystems in original plan:** codegen/, condition/, code_job/, orchestrators/, observers/

### Subsystem Breakdown
- handlers/codegen: 1,433 lines (5 files)
- handlers/person_job: 1,374 lines (5 files)
- handlers/sub_diagram: 2,194 lines (6 files)
- handlers (root): 2,300 lines (8 files)
- Core infrastructure: 2,206 lines (9 files)
- orchestrators/observers: 773 lines (4 files)
- use_cases: 1,115 lines (5 files)

### Refactoring Goals (REVISED)
- Reduce total lines by 23% (13,665 → ~10,500 lines)
- No file over 350 lines (currently 15 files exceed this)
- Eliminate ~800 lines of code duplication
- Clear separation of concerns
- Build reusable utility layer (~390 lines of shared helpers)

---

## Target Directory Structure

### Current Structure (Before)
```
dipeo/application/execution/
├── __init__.py (26 lines)
├── execution_request.py (235 lines) ⚠️
├── reporting.py (82 lines)
├── state_manager.py (326 lines) ⚠️
├── event_pipeline.py (400 lines) ⚠️
├── scheduler.py (328 lines) ⚠️
├── typed_engine.py (430 lines) ⚠️
├── typed_execution_context.py (241 lines)
├── wiring.py (138 lines)
│
├── handlers/
│   ├── __init__.py (51 lines)
│   ├── api_job.py (318 lines) ⚠️
│   ├── db.py (495 lines) ⚠️
│   ├── diff_patch.py (382 lines) ⚠️
│   ├── endpoint.py (160 lines)
│   ├── hook.py (387 lines) ⚠️
│   ├── integrated_api.py (204 lines)
│   ├── start.py (158 lines)
│   ├── user_response.py (145 lines)
│   │
│   ├── core/
│   │   ├── __init__.py (29 lines)
│   │   ├── base.py (168 lines)
│   │   ├── decorators.py (127 lines)
│   │   └── factory.py (122 lines)
│   │
│   ├── codegen/
│   │   ├── __init__.py (26 lines)
│   │   ├── base.py (106 lines)
│   │   ├── ir_builder.py (289 lines)
│   │   ├── schema_validator.py (347 lines) ⚠️
│   │   ├── template.py (361 lines) ⚠️
│   │   └── typescript_ast.py (304 lines)
│   │
│   ├── condition/
│   │   ├── __init__.py (263 lines)
│   │   └── evaluators/
│   │       ├── __init__.py (15 lines)
│   │       ├── base.py (56 lines)
│   │       ├── custom_expression_evaluator.py (60 lines)
│   │       ├── expression_evaluator.py (254 lines)
│   │       ├── llm_decision_evaluator.py (162 lines)
│   │       ├── max_iterations_evaluator.py (92 lines)
│   │       └── nodes_executed_evaluator.py (65 lines)
│   │
│   ├── code_job/
│   │   ├── __init__.py (328 lines)
│   │   └── executors/
│   │       ├── __init__.py (14 lines)
│   │       ├── base.py (94 lines)
│   │       ├── bash_executor.py (121 lines)
│   │       ├── python_executor.py (85 lines)
│   │       └── typescript_executor.py (113 lines)
│   │
│   ├── person_job/
│   │   ├── __init__.py (603 lines) ⚠️
│   │   ├── batch_executor.py (438 lines) ⚠️
│   │   ├── conversation_handler.py (112 lines)
│   │   ├── prompt_resolver.py (97 lines)
│   │   └── text_format_handler.py (124 lines)
│   │
│   └── sub_diagram/
│       ├── __init__.py (344 lines) ⚠️
│       ├── base_executor.py (167 lines)
│       ├── batch_executor.py (542 lines) ⚠️
│       ├── lightweight_executor.py (542 lines) ⚠️
│       ├── parallel_executor.py (301 lines) ⚠️
│       └── single_executor.py (298 lines)
│
├── orchestrators/
│   ├── __init__.py (5 lines)
│   └── execution_orchestrator.py (341 lines) ⚠️
│
├── observers/
│   ├── __init__.py (7 lines)
│   └── metrics_observer.py (420 lines) ⚠️
│
├── states/
│   ├── __init__.py (0 lines)
│   └── execution_state_persistence.py (102 lines)
│
└── use_cases/
    ├── __init__.py (13 lines)
    ├── cli_session.py (182 lines)
    ├── execute_diagram.py (421 lines) ⚠️
    ├── prepare_diagram.py (307 lines) ⚠️
    └── prompt_loading.py (192 lines)

⚠️ = Files >300 lines or requiring refactoring (15 total)
```

### Target Structure (After All Phases)
```
dipeo/application/execution/
├── __init__.py (26 lines)
├── execution_request.py (~195 lines) ✓ Phase 0
├── reporting.py (~70 lines) ✓ Phase 0
├── typed_execution_context.py (241 lines)
├── wiring.py (138 lines)
│
├── state_manager.py (~180 lines) ✓ Phase 0
├── state_snapshot.py (~80 lines) ✓ Phase 0
├── event_log.py (~70 lines) ✓ Phase 0
│
├── scheduler.py (~200 lines) ✓ Phase 2
├── dependency_tracker.py (~80 lines) ✓ Phase 2
├── ready_queue.py (~60 lines) ✓ Phase 2
│
├── typed_engine.py (~280 lines) ✓ Phase 5
├── node_executor.py (~120 lines) ✓ Phase 5
├── engine_helpers.py (~70 lines) ✓ Phase 5
│
├── events/                      # NEW - Phase 0
│   ├── __init__.py
│   ├── pipeline.py (~240 lines) ✓
│   ├── builders.py (~90 lines) ✓
│   └── validators.py (~70 lines) ✓
│
├── handlers/
│   ├── __init__.py (51 lines)
│   ├── endpoint.py (160 lines) ✓
│   ├── start.py (158 lines) ✓
│   ├── user_response.py (145 lines) ✓
│   ├── integrated_api.py (204 lines) ✓ review in Phase 4
│   │
│   ├── core/                    # Handler framework
│   │   ├── __init__.py (29 lines)
│   │   ├── base.py (168 lines)
│   │   ├── decorators.py (127 lines)
│   │   └── factory.py (122 lines)
│   │
│   ├── utils/                   # NEW - Phase 1
│   │   ├── __init__.py
│   │   ├── serialization.py (~80 lines)
│   │   ├── envelope_helpers.py (~90 lines)
│   │   ├── input_helpers.py (~70 lines)
│   │   ├── validation_helpers.py (~60 lines)
│   │   ├── service_helpers.py (~40 lines)
│   │   └── state_helpers.py (~50 lines)
│   │
│   ├── api_job/                 # NEW - Phase 4
│   │   ├── __init__.py
│   │   ├── handler.py (~200 lines)
│   │   └── request_builder.py (~120 lines)
│   │
│   ├── db/                      # NEW - Phase 3c
│   │   ├── __init__.py
│   │   ├── handler.py (~220 lines)
│   │   ├── file_operations.py (~140 lines)
│   │   └── validation.py (~95 lines)
│   │
│   ├── diff_patch/              # NEW - Phase 4
│   │   ├── __init__.py
│   │   ├── handler.py (~200 lines)
│   │   ├── diff_processor.py (~110 lines)
│   │   └── patch_applier.py (~80 lines)
│   │
│   ├── hook/                    # NEW - Phase 4
│   │   ├── __init__.py
│   │   ├── handler.py (~180 lines)
│   │   ├── shell_executor.py (~90 lines)
│   │   ├── webhook_executor.py (~70 lines)
│   │   └── file_executor.py (~60 lines)
│   │
│   ├── codegen/                 # REFACTORED - Phase 3d
│   │   ├── __init__.py (26 lines)
│   │   ├── base.py (106 lines)
│   │   ├── ir_builder.py (289 lines)
│   │   ├── typescript_ast.py (304 lines)
│   │   ├── schema_validator.py (~220 lines) ✓
│   │   ├── validation_rules.py (~130 lines) ✓
│   │   ├── template_engine.py (~200 lines) ✓
│   │   ├── template_helpers.py (~100 lines) ✓
│   │   └── template_validators.py (~70 lines) ✓
│   │
│   ├── condition/               # REVIEWED - Phase 3e
│   │   ├── __init__.py (263 lines) ✓
│   │   └── evaluators/
│   │       ├── __init__.py (15 lines)
│   │       ├── base.py (56 lines)
│   │       ├── custom_expression_evaluator.py (60 lines)
│   │       ├── expression_evaluator.py (254 lines)
│   │       ├── llm_decision_evaluator.py (162 lines)
│   │       ├── max_iterations_evaluator.py (92 lines)
│   │       └── nodes_executed_evaluator.py (65 lines)
│   │
│   ├── code_job/                # REVIEWED - Phase 3f
│   │   ├── __init__.py (328 lines) ✓
│   │   └── executors/
│   │       ├── __init__.py (14 lines)
│   │       ├── base.py (94 lines)
│   │       ├── bash_executor.py (121 lines)
│   │       ├── python_executor.py (85 lines)
│   │       └── typescript_executor.py (113 lines)
│   │
│   ├── person_job/              # REFACTORED - Phase 3a
│   │   ├── __init__.py
│   │   ├── handler.py (~180 lines) ✓
│   │   ├── single_executor.py (~250 lines) ✓
│   │   ├── output_builder.py (~120 lines) ✓
│   │   ├── batch_executor.py (~280 lines) ✓
│   │   ├── batch_helpers.py (~100 lines) ✓
│   │   ├── conversation_handler.py (112 lines)
│   │   ├── prompt_resolver.py (97 lines)
│   │   └── text_format_handler.py (124 lines)
│   │
│   └── sub_diagram/             # REFACTORED - Phase 3b
│       ├── __init__.py
│       ├── handler.py (~200 lines) ✓
│       ├── executor_router.py (~120 lines) ✓
│       ├── base_executor.py (~240 lines) ✓ enhanced
│       ├── single_executor.py (~200 lines) ✓
│       ├── batch_executor.py (~350 lines) ✓
│       ├── lightweight_executor.py (~350 lines) ✓
│       └── parallel_executor.py (~200 lines) ✓
│
├── orchestrators/               # REFACTORED - Phase 2
│   ├── __init__.py (5 lines)
│   ├── execution_orchestrator.py (~220 lines) ✓
│   └── person_cache.py (~100 lines) ✓
│
├── observers/                   # REFACTORED - Phase 2
│   ├── __init__.py (7 lines)
│   ├── metrics_observer.py (~240 lines) ✓
│   ├── metrics_analysis.py (~120 lines) ✓
│   └── metrics_types.py (~80 lines) ✓
│
├── states/
│   ├── __init__.py (0 lines)
│   └── execution_state_persistence.py (102 lines)
│
└── use_cases/                   # REFACTORED - Phase 5
    ├── __init__.py (13 lines)
    ├── cli_session.py (182 lines)
    ├── prompt_loading.py (192 lines)
    ├── execute_diagram.py (~220 lines) ✓
    ├── diagram_preparation.py (~150 lines) ✓
    ├── state_initialization.py (~80 lines) ✓
    ├── prepare_diagram.py (~200 lines) ✓
    └── diagram_compilation.py (~110 lines) ✓

✓ = Refactored/created in phases
```

### Key Structural Changes

**New Directories Created:**
- `events/` - Event pipeline modules (Phase 0)
- `handlers/utils/` - 6 shared utility modules (Phase 1)
- `handlers/api_job/` - Split from api_job.py (Phase 4)
- `handlers/db/` - Split from db.py (Phase 3c)
- `handlers/diff_patch/` - Split from diff_patch.py (Phase 4)
- `handlers/hook/` - Split from hook.py (Phase 4)

**Files Split/Extracted:**
- `state_manager.py` → 3 modules (Phase 0)
- `event_pipeline.py` → 3 modules in `events/` package (Phase 0)
- `scheduler.py` → 3 modules (Phase 2)
- `typed_engine.py` → 3 modules (Phase 5)
- `person_job/__init__.py` → 4 modules (Phase 3a)
- `person_job/batch_executor.py` → 2 modules (Phase 3a)
- `sub_diagram/__init__.py` → 2 modules (Phase 3b)
- `codegen/template.py` → 3 modules (Phase 3d)
- `codegen/schema_validator.py` → 2 modules (Phase 3d)
- `orchestrators/execution_orchestrator.py` → 2 modules (Phase 2)
- `observers/metrics_observer.py` → 3 modules (Phase 2)
- `use_cases/execute_diagram.py` → 3 modules (Phase 5)
- `use_cases/prepare_diagram.py` → 2 modules (Phase 5)

**Files Unchanged (Already Good):**
- All files in `handlers/core/` (framework)
- All files in `handlers/condition/evaluators/` (well-structured)
- All files in `handlers/code_job/executors/` (well-structured)
- Small helper files: conversation_handler, prompt_resolver, text_format_handler
- Infrastructure: wiring.py, typed_execution_context.py, cli_session.py, prompt_loading.py

---

## ✅ Phase 0: Fix Foundation Issues (COMPLETED)

**Status:** ✅ Completed

**Actual Results:**
- execution_request.py: 236 → 184 lines (52 lines saved)
- reporting.py: 83 → 68 lines (15 lines saved)
- state_manager.py split into 3 modules: state_manager.py (281), state_snapshot.py (74), event_log.py (55)
- event_pipeline.py → events/ package: pipeline.py (307), builders.py (104), validators.py (66)
- Created `handlers/utils/` package with service_helpers.py
- All imports updated, tests passing

---

## ✅ Phase 1: Extract Common Utilities (COMPLETED)

**Status:** ✅ Completed

**Actual Results:**
- Created `handlers/utils/` package with 6 comprehensive utility modules
- serialization.py: 74 lines (serialize_data, deserialize_data)
- envelope_helpers.py: 94 lines (create_error_body, create_batch_result_body, create_text_result_body, create_operation_result_body)
- input_helpers.py: 113 lines (extract_first_non_empty, extract_content_value, prepare_template_values, get_input_by_priority)
- validation_helpers.py: 145 lines (validate_file_paths, validate_operation, validate_required_field, validate_config_field)
- service_helpers.py: 62 lines (from Phase 0: has_service, normalize_service_key, resolve_optional/required_service)
- state_helpers.py: 140 lines (get_node_execution_count, get_node_status, get_node_result, has_node_executed, is_node_completed, get_all_node_results)
- __init__.py: 71 lines (exports all 24 utility functions)

**Total:** 699 lines of well-documented, reusable utilities (vs ~390 expected)
- Exceeded expected line count due to comprehensive documentation and examples
- All utilities tested and working correctly
- All code formatted and linted

**Key Achievements:**
- ✓ Comprehensive serialization utilities for JSON/YAML formats
- ✓ Consistent error body and result body builders
- ✓ Powerful input extraction and preparation helpers
- ✓ Reusable validation patterns for common operations
- ✓ Service resolution utilities from Phase 0
- ✓ Complete state query API for execution context
- ✓ Ready for use in subsequent refactoring phases

---

## Phase 2: Core Infrastructure (~250 lines saved)

**Status:** Not started

Refactor core infrastructure components that were missing from original plan:

### 2a. Refactor `scheduler.py` (328 lines → 3 modules)
- [ ] Keep `scheduler.py` - Core NodeScheduler class (~200 lines)
- [ ] Create `dependency_tracker.py` - Indegree/dependency tracking (~80 lines)
- [ ] Create `ready_queue.py` - Queue management and epoch handling (~60 lines)
- **Outcome:** 328 → ~340 lines (better organized)

### 2b. Refactor `orchestrators/execution_orchestrator.py` (341 lines → 2 modules)
- [ ] Keep `execution_orchestrator.py` - Core orchestration (~220 lines)
- [ ] Create `person_cache.py` - Person caching and lifecycle (~100 lines)
- [ ] Integrate with existing prompt_loading use case
- **Outcome:** 341 → ~320 lines (6% reduction)

### 2c. Refactor `observers/metrics_observer.py` (420 lines → 3 modules)
- [ ] Keep `metrics_observer.py` - Core MetricsObserver class (~240 lines)
- [ ] Create `metrics_analysis.py` - Analysis and optimization logic (~120 lines)
- [ ] Create `metrics_types.py` - Data classes (NodeMetrics, ExecutionMetrics) (~80 lines)
- **Outcome:** 420 → ~440 lines (better organized)

**Expected Outcome:**
- ~250 lines saved through extraction and consolidation
- Clear module boundaries for infrastructure
- Better testability for complex components

---

## Phase 3: Handler Subsystems (~800 lines saved)

**Status:** Not started

Comprehensive refactoring of handler subsystems (expanded from original plan):

### 3a. person_job/ (1,374 lines → ~1,000 lines, 27% reduction)

**Split `__init__.py` (603 lines → 4 modules)**
- [ ] Create `handlers/person_job/handler.py` (~180 lines)
  - Main handler class
  - Service injection
  - Coordination logic
- [ ] Create `handlers/person_job/single_executor.py` (~250 lines)
  - `_execute_single()` method
  - Template processing
  - LLM call handling
- [ ] Create `handlers/person_job/output_builder.py` (~120 lines)
  - Output formatting logic
  - Representation building
- [ ] Keep: conversation_handler.py, text_format_handler.py, prompt_resolver.py (already modular)

**Split `batch_executor.py` (438 lines → 2 modules)** *(NEW)*
- [ ] Keep `batch_executor.py` (~280 lines) - Main batch logic
- [ ] Create `batch_helpers.py` (~100 lines) - Batch processing utilities

**Outcome:** 1,374 → ~1,000 lines

### 3b. sub_diagram/ (2,194 lines → ~1,600 lines, 27% reduction)

**Eliminate duplication in executors** *(from original plan)*
- [ ] Extract shared methods to `base_executor.py`:
  - `_create_isolated_registry()` (currently duplicated ~40 lines each)
  - `_register_diagram_persons()` (currently duplicated ~60 lines each)
  - Registry copying utilities (~30 lines)
  - Error formatting (~25 lines)
- [ ] Refactor `lightweight_executor.py`: 542 → ~350 lines
- [ ] Refactor `batch_executor.py`: 542 → ~350 lines

**Split `__init__.py` (344 lines → 2 modules)** *(NEW)*
- [ ] Create `handler.py` (~200 lines) - Main SubDiagramNodeHandler
- [ ] Create `executor_router.py` (~120 lines) - Execution mode routing

**Consolidate parallel/single executors** *(NEW)*
- [ ] Extract ~200 lines of common code to base_executor
- [ ] Reduce `parallel_executor.py`: 301 → ~200 lines
- [ ] Reduce `single_executor.py`: 298 → ~200 lines

**Outcome:** 2,194 → ~1,600 lines

### 3c. db.py (495 lines → 3 modules + utils)

*(from original plan)*
- [ ] Create `handlers/db/` package
- [ ] Implement `handler.py` (~220 lines) - Main handler
- [ ] Implement `file_operations.py` (~140 lines) - File/glob operations
- [ ] Implement `validation.py` (~95 lines) - Validation logic
- [ ] Use `utils/serialization.py` from Phase 1

**Outcome:** 495 → ~455 lines (use shared utils)

### 3d. codegen/ (1,433 lines → ~1,200 lines, 16% reduction) *(NEW)*

**Split `template.py` (361 lines → 3 modules)**
- [ ] Create `template_engine.py` (~200 lines) - Core template processing
- [ ] Create `template_helpers.py` (~100 lines) - Helper functions
- [ ] Create `template_validators.py` (~70 lines) - Template validation

**Split `schema_validator.py` (347 lines → 2 modules)**
- [ ] Keep `schema_validator.py` (~220 lines) - Main validator
- [ ] Create `validation_rules.py` (~130 lines) - Validation rule definitions

**Keep:** typescript_ast.py (304), ir_builder.py (289), base.py (106) - already reasonable

**Outcome:** 1,433 → ~1,200 lines

### 3e. condition/ package (minimal refactor) *(NEW)*
- [ ] Review `__init__.py` (263 lines) - already well-structured
- [ ] Extract common evaluation patterns from evaluators to base if needed
- [ ] Keep evaluator structure (already modular)

**Outcome:** Minimal changes, already well-organized

### 3f. code_job/ package (minimal refactor) *(NEW)*
- [ ] Review `__init__.py` (328 lines) - already well-structured with executor pattern
- [ ] Verify executor implementations are optimal
- [ ] Keep existing structure (already modular)

**Outcome:** Minimal changes, already well-organized

**Phase 3 Total Expected Outcome:**
- ~800 lines saved across all handler subsystems
- All files <350 lines
- Clear module boundaries
- Reduced duplication

---

## Phase 4: Large Single-File Handlers (~300 lines saved) *(NEW)*

**Status:** Not started

Convert monolithic handler files into modular packages:

### 4a. Split `hook.py` (387 lines → 4 modules)
- [ ] Create `handlers/hook/` package
- [ ] Create `handler.py` (~180 lines) - Main HookNodeHandler
- [ ] Create `shell_executor.py` (~90 lines) - Shell command execution
- [ ] Create `webhook_executor.py` (~70 lines) - Webhook/HTTP calls
- [ ] Create `file_executor.py` (~60 lines) - File operations

**Outcome:** 387 → ~400 lines (better organized)

### 4b. Split `diff_patch.py` (382 lines → 3 modules)
- [ ] Create `handlers/diff_patch/` package
- [ ] Create `handler.py` (~200 lines) - Main DiffPatchNodeHandler
- [ ] Create `diff_processor.py` (~110 lines) - Diff parsing and processing
- [ ] Create `patch_applier.py` (~80 lines) - Patch application logic

**Outcome:** 382 → ~390 lines (better organized)

### 4c. Split `api_job.py` (318 lines → 2 modules)
- [ ] Create `handlers/api_job/` package
- [ ] Create `handler.py` (~200 lines) - Main APIJobNodeHandler
- [ ] Create `request_builder.py` (~120 lines) - HTTP request construction

**Outcome:** 318 → ~320 lines (better organized)

### 4d. Review other root handlers *(NEW)*
- [ ] Review `integrated_api.py` (204 lines) - check if splitting needed
- [ ] Review `endpoint.py` (160 lines) - check if splitting needed
- [ ] Review `user_response.py` (145 lines) - likely fine as-is
- [ ] Review `start.py` (158 lines) - likely fine as-is

**Phase 4 Total Expected Outcome:**
- ~300 lines saved through better organization
- All large handlers converted to packages
- Consistent structure across handler types
- Improved maintainability

---

## Phase 5: Core Engine (~250 lines saved)

**Status:** Not started

Refactor execution engine core components (from original plan + additions):

### 5a. Split `typed_engine.py` (430 lines → 3 modules)
- [ ] Keep `typed_engine.py` (~280 lines)
  - Core TypedExecutionEngine orchestration
  - Execution flow control
  - Event pipeline management
- [ ] Create `node_executor.py` (~120 lines)
  - `_execute_single_node()` logic
  - Node execution details
  - Handler invocation
- [ ] Create `engine_helpers.py` (~70 lines)
  - `_extract_llm_usage()` helper
  - `_format_node_result()` helper
  - Utility functions

**Outcome:** 430 → ~470 lines (better organized)

### 5b. Split `use_cases/execute_diagram.py` (421 lines → 3 modules)
- [ ] Keep `execute_diagram.py` (~220 lines)
  - Main ExecuteDiagramUseCase
  - Execution orchestration
  - Update streaming
- [ ] Create `diagram_preparation.py` (~150 lines)
  - `_prepare_and_compile_diagram()` logic
  - Diagram loading and compilation
  - Metadata setup
- [ ] Create `state_initialization.py` (~80 lines)
  - `_initialize_typed_execution_state()` logic
  - State creation
  - Person registration

**Outcome:** 421 → ~450 lines (better organized)

### 5c. Split `use_cases/prepare_diagram.py` (307 lines → 2 modules) *(NEW)*
- [ ] Keep `prepare_diagram.py` (~200 lines)
  - Main PrepareDiagramUseCase
  - Diagram loading orchestration
- [ ] Create `diagram_compilation.py` (~110 lines)
  - Compilation logic
  - Connection resolution

**Outcome:** 307 → ~310 lines (better organized)

**Phase 5 Total Expected Outcome:**
- ~250 lines saved
- Core engine more maintainable
- Clear separation of concerns
- Easier to test individual components

---

## Testing & Verification

After each phase:
- [ ] Run existing tests to ensure no regressions
- [ ] Test affected node types manually
- [ ] Verify imports are correct
- [ ] Check for circular dependencies
- [ ] Run linting and type checking

---

## Final Cleanup

- [ ] Update documentation to reflect new structure
- [ ] Update CLAUDE.md with new architecture
- [ ] Remove any deprecated imports
- [ ] Update type hints if needed
- [ ] Format all new files with ruff

---

## Success Metrics (REVISED)

### Quantitative Goals
- ✅ Total lines: **13,665 → ~10,500** (23% reduction, 3,165 lines saved)
- ✅ Largest file: **603 → ~280 lines** (54% reduction)
- ✅ Files >350 lines: **15 → 0** (eliminate all oversized files)
- ✅ Code duplication: Reduce by **~800 lines**
- ✅ New utility modules: **6 modules, ~390 lines** of reusable code
- ✅ Average file size: **217 → ~150 lines** (31% improvement)

### Subsystem Targets

| Subsystem | Before | After | Reduction |
|-----------|--------|-------|-----------|
| handlers/person_job | 1,374 | ~1,000 | 27% (374 lines) |
| handlers/sub_diagram | 2,194 | ~1,600 | 27% (594 lines) |
| handlers/codegen | 1,433 | ~1,200 | 16% (233 lines) |
| handlers (root) | 2,300 | ~1,600 | 30% (700 lines) |
| Core infrastructure | 2,206 | ~1,800 | 18% (406 lines) |
| orchestrators/observers | 773 | ~650 | 16% (123 lines) |
| use_cases | 1,115 | ~900 | 19% (215 lines) |

### Phase-by-Phase Savings

| Phase | Description | Lines Saved | Status |
|-------|-------------|-------------|--------|
| Phase 0 | Foundation fixes | 67 (actual) | ✅ Done |
| Phase 1 | Common utilities | 699 (reusable) | ✅ Done |
| Phase 2 | Core infrastructure | ~250 | Pending |
| Phase 3 | Handler subsystems | ~800 | Pending |
| Phase 4 | Large handlers | ~300 | Pending |
| Phase 5 | Core engine | ~250 | Pending |
| **Total** | | **~2,366 net** | |

### Qualitative Improvements
- ✅ All files <350 lines (100% compliance)
- ✅ Clear module boundaries and responsibilities
- ✅ Comprehensive reusable utility layer
- ✅ Significantly reduced duplication
- ✅ Improved testability and isolation
- ✅ Better code navigation and discoverability
- ✅ Consistent structure across handler types
- ✅ Easier onboarding and maintenance

---

## Recommended Execution Order

**Priority-based approach for maximum impact:**

1. ✅ **Phase 0** (Foundation) - COMPLETED
   - Fixed critical infrastructure (execution_request, reporting, state_manager, event_pipeline)
   - Established patterns for subsequent phases

2. ✅ **Phase 1** (Utilities) - COMPLETED
   - Created comprehensive shared utilities used by all other phases
   - Enables cleaner refactoring in later phases
   - 699 lines of reusable code with full documentation

3. **Phase 3** (Handlers) - Refactor handler subsystems (biggest impact) ← NEXT
   - Largest line count reduction (~800 lines)
   - Addresses most complex subsystems
   - High user-facing value

4. **Phase 4** (Large handlers) - Convert monolithic handlers
   - Standardizes handler structure
   - Completes handler subsystem modernization

5. **Phase 2** (Infrastructure) - Clean up core infrastructure
   - Builds on utilities from Phase 1
   - Stabilizes infrastructure layer

6. **Phase 5** (Engine) - Refactor execution engine last
   - Core engine changes after handlers are stable
   - Minimizes risk of breaking changes
   - Benefits from all previous refactoring

**Rationale:**
- Utilities available when needed
- High-impact changes early
- Core stability maintained
- Each phase independently testable
- Progressive risk reduction

---

## Audit Findings Summary

### Critical Issues Identified
1. **Line count underestimation:** Original plan claimed 9,392 lines but actual is 13,665 (45% gap)
2. **Missing subsystems:** codegen/, condition/, code_job/, orchestrators/, observers/ not in original plan
3. **Incomplete coverage:** Only 6 of 63 files addressed in original plan (10%)
4. **User-mentioned files missing:** execution_request.py, reporting.py, state_manager.py not covered

### Files >300 Lines Not in Original Plan
- observers/metrics_observer.py (420)
- event_pipeline.py (400)
- hook.py (387)
- diff_patch.py (382)
- codegen/template.py (361)
- codegen/schema_validator.py (347)
- sub_diagram/__init__.py (344)
- orchestrators/execution_orchestrator.py (341)
- scheduler.py (328)
- code_job/__init__.py (328)
- state_manager.py (326)
- api_job.py (318)
- use_cases/prepare_diagram.py (307)

### Plan Improvements
- ✅ Added Phase 0 for foundation issues - **COMPLETED**
- ✅ Expanded Phase 1 with 2 new utilities
- ✅ Added Phase 2 for core infrastructure
- ✅ Expanded Phase 3 to cover ALL handler subsystems
- ✅ Added Phase 4 for large single-file handlers
- ✅ Enhanced Phase 5 with use_cases coverage
- ✅ Updated metrics to reflect actual scope
- ✅ Added execution order guidance

### Completed Work
- **Phase 0**: execution_request.py (52 lines saved), reporting.py (15 lines saved), state_manager split (3 modules), event_pipeline → events/ package (3 modules), handlers/utils/ created
- **Phase 1**: 6 comprehensive utility modules (699 lines total): serialization.py, envelope_helpers.py, input_helpers.py, validation_helpers.py, service_helpers.py, state_helpers.py - all tested, documented, and formatted

---

## Notes

- **Backward Compatibility:** Maintain all existing handler APIs
- **No Breaking Changes:** External interfaces unchanged
- **Gradual Migration:** Each phase is independent and testable
- **Test Coverage:** Verify after each phase, run full test suite
- **Documentation:** Update architecture docs as we refactor
- **Code Review:** Each phase should be reviewed before moving to next
- **Rollback Plan:** Each phase can be reverted independently if issues arise
