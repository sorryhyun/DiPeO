# DiPeO Project Todos

Last updated: 2025-10-11

## Completed (Recent)

### Loop/Cycle Detection ✅ (Completed: 2025-10-11)
**All 4 tasks completed** - Implemented full cycle detection and while loop generation
- [x] Implement graph cycle detection in `_build_execution_order()` (2025-10-11)
  - Added `_detect_loops()` method with DFS and back-edge detection
  - Identifies arrows that create loops
  - Marks nodes that are part of loop bodies

- [x] Generate proper `while` loop structures for detected cycles (2025-10-11)
  - Implemented `_generate_with_loops()` for while loop generation
  - Dynamic indentation system for nested code (2-level indent for loop body)
  - Proper loop body wrapping with condition checks

- [x] Handle condition node integration with loops (2025-10-11)
  - Detects condfalse back-edges (loop continue)
  - Detects condtrue exits (post-loop nodes)
  - Reads max_iteration from person_job nodes in loop

- [x] Add test cases for loop export (2025-10-11)
  - Successfully exported `simple_iter.light.yaml` with correct loop structure
  - Verified iteration counter logic (initialization and increment)
  - Post-loop nodes (ask → endpoint) generated after loop exits

### detect_max_iterations Condition Support ✅ (Completed: 2025-10-11)
**All 4 tasks completed** - Full support for iteration limiting
- [x] Study `detect_max_iterations` condition behavior (2025-10-11)
  - Condition checks iteration count against max limit
  - Reads max_iteration property from nodes in loop
  - Documented in code implementation

- [x] Implement max iteration tracking in exported code (2025-10-11)
  - Generates `iteration_count = 0` initialization
  - Increments counter at end of loop body
  - Tracks counter in node outputs

- [x] Generate condition checks for max iterations (2025-10-11)
  - Generates `while iteration_count < {max_iterations}:` condition
  - Extracts max_iteration from person_job node config
  - Proper loop exit based on counter

- [x] Add test cases for detect_max_iterations (2025-10-11)
  - Verified with `simple_iter.light.yaml` (3 iterations)
  - Correct loop structure with counter logic
  - Test output: `/home/soryhyun/DiPeO/examples/exported/simple_iter_with_loops.py`

### user_response Node Support ✅ (Completed: 2025-10-11)
**All 5 tasks completed** - Interactive user input node export fully functional
- [x] Study user_response node implementation (2025-10-11)
  - Reviewed handler code in `/dipeo/application/execution/handlers/user_response.py`
  - Understood prompt interpolation with `{{variable}}` patterns
  - Documented timeout property usage and edge label mapping
  - Analyzed example diagram: `user_input_demo.light.yaml`

- [x] Implement basic user_response export (2025-10-11)
  - Added `_generate_user_response()` method to `PythonDiagramCompiler`
  - Generates `input()` calls with prompts from node config
  - Creates variables for user responses
  - Tracks outputs in `node_outputs` dict

- [x] Add prompt interpolation support (2025-10-11)
  - Implemented `_interpolate_prompt()` for `{{variable}}` pattern detection
  - Replaces patterns with f-string formatting
  - References upstream node outputs via edge labels
  - Handles missing variables gracefully with fallback values

- [x] Handle timeout property (2025-10-11)
  - Added timeout documentation in generated code comments
  - Noted that timeouts require interactive runtime support
  - Documented limitation in exported Python scripts

- [x] Add test cases for user_response nodes (2025-10-11)
  - Successfully exported `user_input_demo.light.yaml`
  - Tested basic input prompt generation
  - Verified variable interpolation with `{{variable}}` patterns
  - Validated syntactically correct Python output

---

## High Priority

### Metrics Persistence Bug Fix
**Priority: HIGH** | **Estimated effort: Medium**
Critical bug causing metrics data loss despite successful save operations. Race conditions in async checkpoint processing cause database to end up with NULL metrics even when MetricsObserver successfully persists them.

**Problem Summary**:
- `dipeo metrics --latest` shows "No metrics available" even after running with `--timing` or `--debug`
- Logs show successful metrics creation (16 nodes) and persistence
- Database ends up with NULL metrics column due to race conditions

**Root Cause**:
Multiple final checkpoints being created/processed asynchronously. Early checkpoints persist state WITHOUT metrics (before MetricsObserver runs), then later checkpoints or async persistence may overwrite with old cached state that has NULL metrics.

**Evidence from logs**:
```
[PERSIST] exec_47d... NO metrics (metrics=None)  # Multiple times
[MetricsObserver] Created updated_state with metrics: True, node_count=16
[PERSIST] exec_47d... HAS metrics: 16 nodes  # Multiple times
# But database has: metrics = NULL
```

**Files Involved**:
- `/home/soryhyun/DiPeO/dipeo/infrastructure/execution/state/cache_first_state_store.py` - EXECUTION_COMPLETED event handling creates duplicate checkpoints
- `/home/soryhyun/DiPeO/dipeo/application/execution/observers/metrics_observer.py` - Metrics persistence timing
- `/home/soryhyun/DiPeO/dipeo/infrastructure/execution/state/persistence_manager.py` - Database persistence

**Tasks**:
- [ ] Verify attempted fix resolves the issue completely (test with simple_iter diagram)
  - Run: `dipeo run examples/simple_diagrams/simple_iter --light --debug --timing --timeout=40`
  - Verify: `dipeo metrics --latest --breakdown` shows metrics (not "No metrics available")
  - Estimated effort: Small

- [ ] Investigate event subscription ordering and async checkpoint processing
  - Review EventBus subscription priorities
  - Check if checkpoint queue processes in order
  - Identify all places that create final checkpoints
  - Estimated effort: Medium

- [ ] Consider making MetricsObserver run with CRITICAL priority
  - Ensure MetricsObserver runs last before final checkpoint
  - Update event subscription priority if needed
  - Test priority changes don't break other observers
  - Estimated effort: Small

- [ ] Add integration tests for metrics persistence
  - Test that metrics persist correctly after execution
  - Test concurrent checkpoint scenarios
  - Verify database state matches final cached state
  - Estimated effort: Medium

- [ ] Clean up debug logging added during investigation
  - Remove temporary [PERSIST] debug logs
  - Keep useful logging for production debugging
  - Estimated effort: Small

**Testing Command**:
```bash
dipeo run examples/simple_diagrams/simple_iter --light --debug --timing --timeout=40
dipeo metrics --latest --breakdown  # Should show metrics
```

---

## High Priority: Diagram-to-Python Export Enhancements

### Sub-diagram Support
**Priority: Low** | **Estimated effort: Large**
Complex feature for modular diagrams. Lower priority due to complexity.

- [ ] Research sub-diagram implementation in DiPeO
  - Find examples in `projects/codegen/diagrams/`
  - Understand how sub-diagrams are referenced
  - Check parameter passing mechanisms
  - Document return value handling
  - Estimated effort: Medium

- [ ] Design function-based export strategy
  - Each sub-diagram becomes a Python function
  - Generate function signatures from inputs/outputs
  - Handle nested sub-diagram calls
  - Plan module structure for multi-diagram exports
  - Estimated effort: Medium

- [ ] Implement sub-diagram function generation
  - Create separate functions for each sub-diagram
  - Generate parameter lists from input handles
  - Generate return statements from output handles
  - Handle async/await properly
  - Estimated effort: Large

- [ ] Implement sub-diagram call sites
  - Generate function calls in parent diagram
  - Pass arguments from parent context
  - Capture return values
  - Update `node_outputs` tracking
  - Estimated effort: Medium

- [ ] Add test cases for sub-diagrams
  - Simple sub-diagram with single input/output
  - Sub-diagram with multiple parameters
  - Nested sub-diagram calls
  - Sub-diagram with shared state
  - Estimated effort: Large

## Code Quality & Testing

### Export Feature Testing
**Priority: Medium** | **Estimated effort: Medium**

- [ ] Create test suite for export functionality
  - Unit tests for `PythonDiagramCompiler` class
  - Integration tests for complete diagram exports
  - Test fixtures for various diagram patterns
  - Estimated effort: Large

- [ ] Add validation for exported scripts
  - Syntax validation (compile exported code)
  - Static analysis with pylint/ruff
  - Test execution in isolated environment
  - Estimated effort: Medium

- [ ] Create example gallery
  - Export all examples from `examples/simple_diagrams/`
  - Document expected vs actual behavior
  - Add to documentation with before/after code
  - Estimated effort: Small

## Documentation Updates

### Export Feature Documentation
**Priority: Low** | **Estimated effort: Small**

- [ ] Update `docs/features/diagram-to-python-export.md`
  - Add loop/cycle detection section
  - Document detect_max_iterations support
  - Add user_response examples
  - Update limitations section
  - Estimated effort: Small

- [ ] Add troubleshooting guide
  - Common export issues and solutions
  - Manual adjustments that may be needed
  - Debugging tips for exported scripts
  - Estimated effort: Small

- [ ] Create export best practices guide
  - Which diagram patterns export well
  - Patterns that need manual adjustment
  - How to structure diagrams for clean export
  - Estimated effort: Medium

---

## Notes

- **Test as you go**: Each feature should have test cases before marking complete
- **Backward compatibility**: Not a priority per project guidelines
- **Code comments**: Avoid excessive comments, keep code self-documenting
- **Generated files**: Don't edit directly, modify generation logic

## Quick Reference

- **Export implementation**: `/home/soryhyun/DiPeO/dipeo/domain/diagram/compilation/python_compiler.py`
- **Export command**: `dipeo export <diagram> <output.py> [--light]`
- **Test command**: `dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=40`
- **Documentation**: `/home/soryhyun/DiPeO/docs/features/diagram-to-python-export.md`
- **Example diagrams**: `/home/soryhyun/DiPeO/examples/simple_diagrams/`

## Total Tasks Summary

- **Completed**: 13 tasks ✅
  - 4 loop/cycle detection
  - 4 detect_max_iterations
  - 5 user_response node support
- **High Priority**: 7 tasks (5 metrics bug fix + 2 quality/testing)
- **Low Priority**: 7 tasks (5 sub-diagram + 2 documentation)

**Total**: 14 remaining tasks | 13 completed | 27 total across 5 major feature areas

**Recent progress**: Added critical metrics persistence bug fix (2025-10-11) - race conditions causing database to have NULL metrics despite successful MetricsObserver saves
