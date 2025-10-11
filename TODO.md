# DiPeO Project Todos

Last updated: 2025-10-11

## Overview

This TODO list focuses on refactoring the `dipeo/domain/diagram/` directory to improve maintainability and match the code quality of the execution domain. Tasks are organized by priority and timeline.

**Total workload**: 6 major refactoring tasks across 1-2 months
- Quick Wins: 2 tasks (Week 1-2)
- High-Value Refactors: 4 tasks (Month 1-2)
- Optional Improvements: Included in task 6

---

## High Priority - Quick Wins (Week 1-2)

### Task 1: Split strategy_common.py into separate files ✓
**Estimated effort: Small** | **Completed: 2025-10-11**

The `dipeo/domain/diagram/utils/strategy_common.py` file contains multiple utility classes that should be separated for better organization and maintainability.

- [x] Move NodeFieldMapper to `utils/node_field_mapper.py`
  - Extract class definition and related functions
  - Add appropriate module docstring

- [x] Move HandleParser to `utils/handle_parser.py`
  - Extract class definition and related functions
  - Add appropriate module docstring

- [x] Move PersonExtractor to `utils/person_extractor.py`
  - Extract class definition and related functions
  - Add appropriate module docstring

- [x] Move ArrowDataProcessor to `utils/arrow_data_processor.py`
  - Extract class definition and related functions
  - Add appropriate module docstring

- [x] Update imports in all strategy files
  - Update `strategies/readable_strategy.py`
  - Update `strategies/light_strategy.py`
  - Update any other files that import from strategy_common

- [x] Run tests to verify no regressions
  - Run: `make lint-server`
  - Test diagram parsing with both formats
  - Verify no import errors

**Files to modify**:
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/strategy_common.py`
- New files: `node_field_mapper.py`, `handle_parser.py`, `person_extractor.py`, `arrow_data_processor.py`
- All files in `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/`

---

### Task 2: Extract flow parsing from readable_strategy.py ✓
**Estimated effort: Small** | **Completed: 2025-10-11**

The `readable_strategy.py` file handles both old and new format parsing. Extract flow parsing logic to a dedicated module.

- [x] Create `strategies/readable/flow_parser.py`
  - Create new subdirectory if needed
  - Add module for flow parsing logic

- [x] Move old format parsing methods
  - Extract methods that handle legacy flow format
  - Maintain backward compatibility

- [x] Move new format parsing methods
  - Extract methods that handle current flow format
  - Ensure consistent interface

- [x] Update main strategy to use the new parser
  - Import and instantiate FlowParser
  - Delegate flow parsing calls
  - Keep strategy class focused on orchestration

- [x] Add tests for flow parser
  - Test old format parsing
  - Test new format parsing
  - Test format detection

**Files modified**:
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/readable_strategy.py` (removed 259 lines)
- New file: `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/readable/flow_parser.py` (13KB)
- New file: `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/readable/__init__.py`

---

## Medium Priority - High-Value Refactors (Month 1-2)

### Task 3: Complete refactor of readable_strategy.py ✓
**Estimated effort: Large** | **Completed: 2025-10-11**

Transform `readable_strategy.py` into a well-organized subdirectory structure with clear separation of concerns.

- [x] Create subdirectory structure `strategies/readable/`
  - Create directory if not exists
  - Plan file organization

- [x] Create `strategies/readable/strategy.py`
  - Main orchestration class
  - High-level parse/serialize methods
  - Delegates to specialized modules

- [x] Create `strategies/readable/parser.py`
  - Node parsing logic
  - Connection parsing logic
  - Data extraction methods

- [x] Create `strategies/readable/flow_parser.py`
  - Old format flow parsing (from Task 2)
  - New format flow parsing
  - Format detection logic

- [x] Create `strategies/readable/serializer.py`
  - Diagram serialization logic
  - Output formatting
  - Data structuring methods

- [x] Create `strategies/readable/transformer.py`
  - Data transformation logic
  - Format conversion methods
  - Validation logic

- [x] Update all imports and references
  - Update strategy registry
  - Update tests
  - Update documentation

- [x] Maintain backward compatibility
  - Ensure existing diagrams still parse
  - Test with various diagram formats

- [x] Add comprehensive tests
  - Unit tests for each module
  - Integration tests for full flow
  - Test edge cases and error handling

**Files modified**:
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/readable_strategy.py` (converted to forwarding module)
- New directory: `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/readable/`
- New files: `strategy.py`, `parser.py`, `flow_parser.py`, `serializer.py`, `transformer.py`, `__init__.py`

---

### Task 4: Refactor light_strategy.py ✓
**Estimated effort: Large** | **Completed: 2025-10-11**

Applied similar subdirectory structure to `light_strategy.py` for consistency and maintainability.

- [x] Create subdirectory structure `strategies/light/`
- [x] Create `strategies/light/strategy.py` - Main orchestration class
- [x] Create `strategies/light/parser.py` - Node parsing logic and data extraction
- [x] Create `strategies/light/connection_processor.py` - Connection parsing and handle resolution
- [x] Create `strategies/light/serializer.py` - Diagram serialization to light format
- [x] Update all imports and references
- [x] Add comprehensive tests

**Files modified**:
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/light_strategy.py` (converted to forwarding module)
- New directory: `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/light/`
- New files: `strategy.py`, `parser.py`, `connection_processor.py`, `serializer.py`, `__init__.py`

**Completion notes**:
- All linting and type checks pass
- Tested successfully with example diagrams (`simple_iter`)
- Export functionality validated (`dipeo export`)
- Backward compatibility maintained via forwarding module

---

### Task 5: Extract compilation phases from domain_compiler.py
**Estimated effort: Large**

Break down the compilation process into distinct, testable phases for better maintainability and extensibility.

- [ ] Create `compilation/phases/` directory
  - Create directory structure
  - Plan phase organization

- [ ] Create ValidationPhase class
  - Diagram structure validation
  - Node validation
  - Connection validation
  - Return validation results

- [ ] Create NodeTransformationPhase class
  - Node data transformation
  - Type conversion
  - Property mapping

- [ ] Create ConnectionResolutionPhase class
  - Resolve handle connections
  - Build connection graph
  - Validate connection integrity

- [ ] Create additional phase classes as needed
  - Identify other compilation phases
  - Create phase classes with clear interfaces
  - Document phase responsibilities

- [ ] Update domain_compiler to orchestrate phases
  - Refactor main compilation method
  - Call phases in sequence
  - Handle phase errors appropriately

- [ ] Add phase-specific tests
  - Unit tests for each phase
  - Test phase isolation
  - Test phase composition

- [ ] Document compilation pipeline
  - Document phase order
  - Document phase dependencies
  - Document error handling

**Files to modify**:
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/domain_compiler.py`
- New directory: `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/phases/`
- New files: `validation_phase.py`, `node_transformation_phase.py`, `connection_resolution_phase.py`, etc.

---

### Task 6: Simplify python_compiler.py
**Estimated effort: Medium** (Optional Improvement)

Extract complex logic from `python_compiler.py` to improve readability and testability.

- [ ] Extract loop detection to separate file
  - Create `compilation/python_export/loop_detector.py`
  - Move loop detection algorithms
  - Move cycle detection logic

- [ ] Extract code generation logic
  - Create `compilation/python_export/code_generator.py`
  - Move code generation methods
  - Move output formatting logic

- [ ] Create `compilation/python_export/` subdirectory
  - Organize python export functionality
  - Group related modules
  - Improve discoverability

- [ ] Refactor main python_compiler.py
  - Keep as orchestration layer
  - Delegate to specialized modules
  - Simplify main compilation flow

- [ ] Add tests for extracted modules
  - Test loop detection independently
  - Test code generation independently
  - Test integration with main compiler

**Files to modify**:
- `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/python_compiler.py`
- New directory: `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/python_export/`
- New files: `loop_detector.py`, `code_generator.py`

---

## Testing Strategy

For all refactoring tasks, follow this testing approach:

1. **Before refactoring**: Run existing tests to establish baseline
   - `make lint-server`
   - Test diagram parsing: `dipeo run examples/simple_diagrams/simple_iter --light --debug`

2. **During refactoring**: Run tests frequently
   - After each file split
   - After each import update

3. **After refactoring**: Comprehensive validation
   - All existing tests pass
   - No regressions in functionality
   - Code quality improves (lint, type checking)

**Test commands**:
```bash
# Lint and format
make lint-server
make format

# Type checking
pnpm typecheck

# Test diagram execution
dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=40
dipeo export examples/simple_diagrams/simple_iter.light.yaml output.py --light

# GraphQL schema validation
make graphql-schema
```

---

## Goal

Improve maintainability of the diagram domain to match the quality of the execution domain (which needs no refactoring). Focus on:
- Clear separation of concerns
- Better module organization
- Improved testability
- Reduced complexity in individual files
- Consistent architecture patterns

---

## Progress Summary

- **Completed**: 4 tasks (Tasks 1-4) - 27 action items ✓
- **High Priority (Quick Wins)**: 0 tasks remaining - All quick wins completed! 🎉
- **Medium Priority (High-Value)**: 2 tasks remaining (Tasks 5-6) - 22 action items
- **Total**: 6 major tasks (67% complete) - 49 total action items (27 completed, 22 remaining)

**Current Status**: Tasks 1-4 completed successfully on 2025-10-11. Both strategy files (`readable_strategy.py` and `light_strategy.py`) have been completely refactored into modular subdirectory structures with clear separation of concerns:

**Readable Strategy** (Task 3):
- **Parser**: Node and connection parsing
- **Transformer**: Data transformations between formats
- **Serializer**: Diagram export and serialization
- **Strategy**: Main orchestrator
- **Flow Parser**: Legacy and current flow format handling

**Light Strategy** (Task 4):
- **Parser**: Node parsing and data extraction
- **Connection Processor**: Connection parsing and handle resolution
- **Serializer**: Light format serialization
- **Strategy**: Main orchestrator

All modules are well-organized, maintainable, and pass linting checks. Backward compatibility is maintained via forwarding modules.

**Next Recommended Task**: Task 5 - Extract compilation phases from domain_compiler.py (Large effort, will improve compilation pipeline maintainability)

**Timeline**: 1-2 months for complete refactoring
- Week 1-2: Quick wins (Tasks 1-2) ✓ COMPLETE
- Week 3-4: Complete readable strategy refactor (Task 3) ✓ COMPLETE
- Week 5-6: Complete light strategy refactor (Task 4) ✓ COMPLETE
- Week 7-8: High-value refactors (Tasks 5-6)

**Note**: Tasks can be worked on incrementally. Each completed subtask improves the codebase immediately.
