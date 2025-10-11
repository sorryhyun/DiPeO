# DiPeO Project Todos

Last updated: 2025-10-11

## Overview

This document tracks active refactoring tasks for DiPeO's domain layer.

**Current Status:**
- Diagram Module Refactoring (Phases 1-3): COMPLETE
- Execution Module Refactoring (Phase 5): In Progress (6/11 tasks - Sprint 1 COMPLETE, Sprint 2-3 2/3 complete - 67%)
- Optional Future Improvements (Phase 4): Not started (0/6 tasks)

**Recent Achievement:**
- **Sprint 1 COMPLETE (2025-10-11):** Execution module foundation refactored
  - Reorganized into 5 subdirectories (state/, tokens/, rules/, messaging/, context/)
  - Fixed README documentation mismatches (448 lines + 3,043 lines in subdirectories)
  - Extracted TokenReadinessEvaluator from 94-line TokenManager method
  - All tests passing, 50+ imports updated
- Diagram module (dipeo/domain/diagram/) fully refactored with ~571 lines eliminated
- Configuration-driven design patterns implemented (HandleSpec, FIELD_MAPPINGS)
- 6-phase compilation pipeline extracted

**Recent Progress:**
- **Task 32 COMPLETE (2025-10-11):** UnifiedStateTracker implementation successful
  - Created UnifiedStateTracker consolidating ExecutionTracker and StateTracker
  - Eliminated critical issue of two divergent sources of truth for state tracking
  - Implemented thread-safe operations with internal locking (RLock)
  - Maintained 100% backward compatibility (old names are aliases)
  - All 44 unit tests passing (100% pass rate)
  - Integration test with simple_iter diagram successful
  - Comprehensive documentation (5 documents, 55+ KB)
  - Completed in ~4 hours (under 16-20 hour estimate)
- **Task 31 COMPLETE (2025-10-11):** ExecutionRuleRegistry pattern implemented
  - Created ExecutionRuleRegistry with pluggable, extensible rule system
  - Implemented thread-safe registry with audit trails, priority system, and immutability
  - Created comprehensive adapters for existing connection and transform rules
  - Maintained 100% backward compatibility through existing rule classes
  - All 32 unit tests passing, integration test successful
  - Completed in ~6 hours (under 12-16 hour estimate)
- **Task 30 ARCHIVED (2025-10-11):** TokenManager refactoring completed and archived
  - Created tokens/policies.py with JoinPolicyType enum, JoinPolicyEvaluator, TokenCounter
  - Refactored TokenManager to use TokenCounter for all token counting
  - All tests passing, linter clean

**Next Focus:**
- Sprint 2-3: Task 33 (Expand ExecutionContext Protocol) - final Sprint 2-3 task
- Based on comprehensive audit report (report.md, 2025-10-11)

---

## Active Tasks

### Phase 5: Execution Module Refactoring

Based on audit report findings, the execution module requires moderate-to-substantial refactoring to achieve consistency with the diagram module's architecture.

---

#### Sprint 2-3: High Priority Improvements

---

##### Task 31: Implement ExecutionRuleRegistry Pattern (HIGH-2) ✓ COMPLETE
**Priority:** HIGH | **Effort:** Large (12-16 hours) | **Actual:** ~6 hours
**Completed:** 2025-10-11

Create a registry pattern for connection rules and transform rules to enable extensibility.

**Actions Completed:**
- [x] Create `rules/rule_registry.py` with ExecutionRuleRegistry class
- [x] Define ConnectionRule protocol/base class
- [x] Define TransformRule protocol/base class
- [x] Implement registry methods: register_connection_rule, register_transform_rule
- [x] Implement get_applicable_transforms method
- [x] Refactor NodeConnectionRules to use registry (via adapters)
- [x] Refactor DataTransformRules to use registry (via adapters)
- [x] Update resolution module to query registry
- [x] Add comprehensive unit tests (32 tests passing)
- [x] Validate integration with simple_iter diagram

**Implementation Details:**
- Created ExecutionRuleRegistry with thread-safe operations (RLock)
- Implemented priority-based rule ordering system
- Added audit trail tracking (registration time, caller info)
- Created adapters for backward compatibility with existing rule classes
- Maintained 100% backward compatibility (no breaking changes)
- Comprehensive test suite covering all rule types and scenarios

**Files:**
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/execution/rules/rule_registry.py` (520 lines)
- NEW: `/home/soryhyun/DiPeO/tests/unit/domain/execution/rules/test_rule_registry.py` (1,062 lines)
- MODIFIED: `/home/soryhyun/DiPeO/dipeo/domain/execution/rules/__init__.py` (added exports)

**Note:** Kept in active section (will archive at sprint completion)

---

##### Task 32: Unify State Tracking (HIGH-3) ✓ COMPLETE
**Priority:** HIGH | **Effort:** Large (16-20 hours) | **Actual:** ~4 hours
**Completed:** 2025-10-11

Merge ExecutionTracker and StateTracker to eliminate redundant state tracking and synchronization risks.

**Original Issue:**
- ExecutionTracker and StateTracker had overlapping responsibilities
- Execution count tracked in two places
- Two sources of truth could diverge
- Unclear ownership of state data

**Actions Completed:**
- [x] Design unified UnifiedStateTracker architecture (simplified from original 3-class design)
- [x] Create `state/unified_state_tracker.py` with UnifiedStateTracker class
- [x] Consolidate ExecutionTracker and StateTracker logic into single class
- [x] Implement thread-safe operations with internal locking (RLock)
- [x] Maintain 100% backward compatibility (ExecutionTracker, StateTracker as aliases)
- [x] Update all direct references to use UnifiedStateTracker
- [x] Preserve old classes as aliases for backward compatibility
- [x] Update ExecutionContext to use UnifiedStateTracker
- [x] Add comprehensive unit tests (44 tests, 100% pass rate)
- [x] Validate integration with simple_iter diagram
- [x] Create comprehensive documentation (5 documents, 55+ KB)

**Implementation Details:**
- Created UnifiedStateTracker consolidating all state tracking responsibilities
- Thread-safe design with RLock for concurrent access
- Single source of truth for execution count and node state
- Backward compatible through type aliases (no breaking changes)
- Comprehensive test suite covering all state operations and thread safety
- Integration test successful with example diagrams

**Files:**
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/execution/state/unified_state_tracker.py` (450 lines)
- NEW: `/home/soryhyun/DiPeO/tests/unit/domain/execution/state/test_unified_state_tracker.py` (1,285 lines)
- NEW: `/home/soryhyun/DiPeO/docs/architecture/execution-state-tracking.md` (comprehensive docs)
- MODIFIED: `/home/soryhyun/DiPeO/dipeo/domain/execution/state/__init__.py` (updated exports)
- MODIFIED: `/home/soryhyun/DiPeO/dipeo/domain/execution/execution_context.py` (uses UnifiedStateTracker)

**Note:** Kept in active section (will archive at sprint completion)

---

##### Task 33: Expand ExecutionContext Protocol (MED-1)
**Priority:** MEDIUM | **Effort:** Small (4-6 hours)

Expand ExecutionContext protocol to provide complete abstraction and reduce direct manager access.

**Current Issue:**
- Protocol exists but most code directly accesses `ctx.state` and `ctx.tokens`
- Abstraction benefits underutilized

**Actions:**
- [ ] Add convenience methods to ExecutionContext protocol:
  - get_node_output()
  - get_node_status()
  - has_completed()
  - mark_node_completed()
- [ ] Update protocol implementations
- [ ] Refactor resolution module to use protocol methods instead of direct access
- [ ] Update documentation with protocol usage examples

**Files:**
- `/home/soryhyun/DiPeO/dipeo/domain/execution/execution_context.py`
- `/home/soryhyun/DiPeO/dipeo/domain/execution/resolution/` (various files)

---

#### Sprint 4+: Long-term Improvements

---

##### Task 34: Implement Domain Events System (MED-3)
**Priority:** MEDIUM | **Effort:** Medium (8-12 hours)

Add domain events for state transitions to enable audit trails, monitoring, and decoupled side effects.

**Actions:**
- [ ] Create `events/execution_events.py` with domain event classes:
  - NodeExecutionStarted
  - NodeExecutionCompleted
  - NodeExecutionFailed
  - TokenProduced
  - TokenConsumed
- [ ] Add EventBus integration to StateTracker
- [ ] Emit events on all state transitions
- [ ] Update documentation with event patterns
- [ ] Add event-based testing examples

**Files:**
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/execution/events/execution_events.py`
- MODIFY: `/home/soryhyun/DiPeO/dipeo/domain/execution/state/` (state management files)

---

##### Task 35: Improve Type Discipline (MED-4)
**Priority:** MEDIUM | **Effort:** Small (6-8 hours)

Replace liberal use of `Any` with precise type hints.

**Actions:**
- [ ] Define TransformRules TypedDict or protocol
- [ ] Replace `Any` in transform_rules.py with specific types
- [ ] Replace `Any` in resolution/api.py extract_edge_value() signature
- [ ] Add missing return type hints
- [ ] Create types.py for common type definitions
- [ ] Run `pnpm typecheck` to verify improvements

**Files:** Multiple files in `/home/soryhyun/DiPeO/dipeo/domain/execution/`

---

##### Task 36: Modernize EnvelopeFactory API (MED-2)
**Priority:** LOW | **Effort:** Small (3-4 hours)

Refactor EnvelopeFactory to use explicit class methods instead of auto-detection.

**Actions:**
- [ ] Add class methods: from_text(), from_json(), from_binary(), from_conversation()
- [ ] Add from_error() class method for error envelopes
- [ ] Keep auto_detect() for backward compatibility
- [ ] Update call sites to use explicit methods
- [ ] Add docstrings with usage examples

**Files:** `/home/soryhyun/DiPeO/dipeo/domain/execution/envelope.py:130-175`

---

##### Task 37: Performance Optimizations
**Priority:** LOW | **Effort:** Medium (8-10 hours)

Optimize token management and state tracking performance.

**Actions:**
- [ ] Add `slots=True` to Token dataclass for memory efficiency
- [ ] Profile token placement and retrieval operations
- [ ] Optimize token storage data structures if needed
- [ ] Add benchmarking tests for large diagram executions
- [ ] Document performance characteristics in README

**Files:** `/home/soryhyun/DiPeO/dipeo/domain/execution/token_types.py`

---

### Phase 4: Diagram Module Future Improvements (Low Priority)

These tasks are optional enhancements for the diagram module. Can be prioritized based on development needs.

---

#### Task 18: Convert YAML/JSON Mixins to Base Classes
**Priority:** LOW | **Effort:** Small (2-3 hours)

`_JsonMixin` and `_YamlMixin` should be explicit base classes rather than mixins.

**Actions:**
- [ ] Create `YamlConversionStrategy` and `JsonConversionStrategy` base classes
- [ ] Refactor strategy hierarchy in `/home/soryhyun/DiPeO/dipeo/domain/diagram/utils/conversion_utils.py`
- [ ] Update all strategy classes to inherit from new base classes
- [ ] Test all strategies still work

---

#### Task 19: Add Testing Utilities for Diagram Module
**Priority:** LOW | **Effort:** Medium (3-4 hours)

Create test factories and fixtures for diagram module.

**Actions:**
- [ ] Create `/home/soryhyun/DiPeO/dipeo/domain/diagram/testing/` directory
- [ ] Create `factories.py` with `DiagramFactory` class
- [ ] Create `fixtures.py` with common test fixtures
- [ ] Create `assertions.py` with custom assertions
- [ ] Document usage in developer guide

---

#### Task 20: Improve Type Hints Consistency for Diagram Module
**Priority:** LOW | **Effort:** Small (2-3 hours)

Create TypedDict types for common diagram structures.

**Actions:**
- [ ] Create `/home/soryhyun/DiPeO/dipeo/domain/diagram/models/types.py`
- [ ] Define TypedDict types: NodeDict, ArrowDict, HandleDict, PersonDict
- [ ] Update function signatures to use TypedDict
- [ ] Run `pnpm typecheck`

---

#### Task 21: Eliminate Magic Strings for Node Types
**Priority:** LOW | **Effort:** Small (1-2 hours)

Replace string comparisons with enum usage.

**Actions:**
- [ ] Create `NodeTypeChecker` helper class
- [ ] Search for all magic string comparisons
- [ ] Update to use `NodeType` enum
- [ ] Run tests

---

#### Task 22: Automate Strategy Registration
**Priority:** LOW | **Effort:** Small (2-3 hours)

Use registry pattern with auto-discovery for diagram strategies.

**Actions:**
- [ ] Create `/home/soryhyun/DiPeO/dipeo/domain/diagram/strategies/registry.py`
- [ ] Create `StrategyRegistry` class with auto-discovery
- [ ] Add `@StrategyRegistry.register` decorator
- [ ] Implement auto-discovery using importlib
- [ ] Update strategy instantiation

---

## Progress Summary

**Overall:** 2/13 active tasks complete (15.4%)

**By Phase:**
- Phase 4 (Diagram Optional): 0/6 (0%) - Not started
- Phase 5 (Execution Sprint 1): 3/3 (100%) - **COMPLETE** (Archived)
- Phase 5 (Execution Sprint 2-3): 2/3 (67%) - In Progress (Tasks 31-32 complete, Task 33 remaining)
- Phase 5 (Execution Sprint 4+): 0/4 (0%) - Not started

**Priority Breakdown:**
- CRITICAL: 0 tasks (Sprint 1 complete, archived)
- HIGH: 1 remaining task (Task 33), 2 complete (Tasks 31-32)
- MEDIUM: 2 tasks (Tasks 34-35)
- LOW: 8 tasks (Tasks 18-22, 36-37, and Phase 4 optional)

**Estimated Effort:**
- Sprint 1 (Immediate): COMPLETE (~12 hours actual, archived)
- Sprint 2-3 (Short-term): ~4-6 hours remaining (1 task: 33) - Tasks 31 (~6h) and 32 (~4h) complete
- Sprint 4+ (Long-term): 25-34 hours (4 tasks: 34-37)
- Phase 4 (Optional): 13-18 hours (5 tasks: 18-22)
- **Remaining:** ~42-58 hours (5-7 days full-time)

---

## Testing Strategy

### Before Refactoring
```bash
make lint-server
dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=40
```

### During Refactoring
- Run tests after each file modification
- Commit after each completed task
- Test incrementally
- Check `.dipeo/logs/cli.log` for execution details

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
- All Sprint 1-3 tasks complete (7/11 execution tasks)
- Execution module organized into subdirectories (state/, tokens/, rules/, messaging/, context/)
- Token manager decomposed from 1 complex method to 5+ focused methods
- State tracking unified into single ExecutionState class
- ExecutionRuleRegistry implemented for extensibility

**Qualitative:**
- Execution module matches diagram module's organizational quality
- Clear separation of concerns (state management, token control, business rules)
- Improved testability through smaller, focused components
- Extensible architecture via registry patterns
- Documentation accurate and comprehensive
- Type safety improved with reduced `Any` usage
- Consistent patterns across domain layer

---

## Completed Work Archive

### Phase 5, Sprint 2-3: TokenManager Refactoring (COMPLETE - 2025-10-11)

**Task 30: Complete TokenManager Refactoring (HIGH-1, Part 2)**
**Priority:** HIGH | **Effort:** Medium (4-6 hours actual)
**Completed:** 2025-10-11

Continued TokenManager refactoring by extracting additional responsibilities into separate, focused components.

**Actions Completed:**
- [x] Extracted token policy logic into `tokens/policies.py`
- [x] Created JoinPolicyType enum for "all", "any", "first", "k_of_n" policies
- [x] Extracted token counting logic into separate TokenCounter class
- [x] Refactored token placement logic for better testability
- [x] Added comprehensive docstrings to all token-related classes
- [x] Reviewed and optimized token storage data structures

**Implementation Details:**
- Created `dipeo/domain/execution/tokens/policies.py` with:
  - JoinPolicyType enum (ALL, ANY, FIRST, K_OF_N)
  - JoinPolicyEvaluator class for policy evaluation logic
  - TokenCounter class for token counting and consumption tracking
  - TokenAvailabilityChecker protocol for dependency injection
- Refactored TokenManager to use TokenCounter for all token counting operations
- Refactored TokenReadinessEvaluator to use JoinPolicyEvaluator for policy evaluation
- Updated `tokens/__init__.py` exports (JoinPolicyType, JoinPolicyEvaluator, TokenCounter)
- All tests pass (validated with simple_iter diagram)
- Code passes linter checks (ruff)

**Impact:**
- Better separation of concerns (token counting, policy evaluation, token management)
- Improved testability and maintainability
- TokenManager is cleaner and more focused on core responsibilities
- Policy evaluation logic now isolated and easier to extend

**Files Modified:**
- NEW: `/home/soryhyun/DiPeO/dipeo/domain/execution/tokens/policies.py` (3 new classes)
- MODIFIED: `/home/soryhyun/DiPeO/dipeo/domain/execution/tokens/token_manager.py`
- MODIFIED: `/home/soryhyun/DiPeO/dipeo/domain/execution/tokens/token_readiness_evaluator.py`
- MODIFIED: `/home/soryhyun/DiPeO/dipeo/domain/execution/tokens/__init__.py`

**Verification:**
- All linting/type checks passing
- Integration tests passing: `dipeo run examples/simple_diagrams/simple_iter --light --debug`
- TokenCounter properly handles token counting and consumption tracking
- JoinPolicyEvaluator correctly evaluates all policy types

---

### Phase 5, Sprint 1: Execution Module Foundation (COMPLETE - 2025-10-11)

**Summary:**
- 3/3 tasks completed (Tasks 27-29)
- Execution module reorganized into 5 subdirectories
- Documentation rewritten from scratch (448 → 3,491 total lines)
- TokenManager method extracted into focused TokenReadinessEvaluator class
- All tests passing, backward compatibility maintained

**Key Achievements:**
- **Task 27:** Created subdirectories: state/, tokens/, rules/, messaging/, context/
  - Moved 8 files using git mv (preserved history)
  - Created 5 __init__.py files with proper exports
  - Updated 50+ import statements across codebase
- **Task 28:** Fixed README documentation mismatches
  - Rewrote main README.md (554 → 448 lines)
  - Created 5 subdirectory READMEs (3,043 lines total)
  - Removed aspirational features, documented actual implementation
- **Task 29:** Refactored TokenManager.has_new_inputs() method
  - Extracted 94-line method into TokenReadinessEvaluator class
  - Created 4 focused methods: _get_relevant_edges, _filter_by_conditions, _evaluate_join_policy, has_new_inputs
  - Improved testability and SRP compliance

**Verification:**
- All linting/type checks passing
- Integration tests passing: `dipeo run examples/simple_diagrams/simple_iter --light --debug`
- Backward compatibility maintained through __init__.py exports

---

### Phase 1-3: Diagram Module Refactoring (COMPLETE - 2025-10-11)

**Summary:**
- 15/15 tasks completed
- ~571 lines eliminated across diagram module
- Configuration-driven design patterns implemented
- 6-phase modular compilation pipeline extracted
- Validation architecture consolidated (structural vs business)
- Utility module reorganized into subdirectories
- Comprehensive documentation added

**Key Achievements:**
- HandleSpec dataclass and HANDLE_SPECS mapping created
- FIELD_MAPPINGS configuration for table-driven field mapping
- Phase classes extracted: ValidationPhase, NodeTransformationPhase, EdgeBuildingPhase, etc.
- Strategies standardized: parser → transformer → serializer → strategy
- Person-related logic unified into utils/person/ subdirectory
- Port interfaces cleaned to follow SRP
- 5 deprecated modules removed

**Verification:**
- All linting/type checks passing
- Example diagrams run successfully
- Architecture documented in docs/architecture/
- Developer guide updated

**Based on:** Comprehensive codebase audit (2025-10-11), 54 Python files in `dipeo/domain/diagram/`

---

## Notes

- **Status:** Execution module refactoring in progress (Phase 5)
- **Based on:** Comprehensive audit report (report.md, 2025-10-11)
- **Audit scope:** 20 Python files in `dipeo/domain/execution/`
- **Risk level:** Low - Changes follow established patterns from diagram module
- **ROI:** High (improved maintainability, extensibility, consistency)
- **Backward Compatibility:** Maintain through careful __init__.py exports

**Important:** Sprint 1 tasks (Tasks 27-29) should be completed first as they set the foundation for all subsequent work. Sprint 2-3 tasks build on Sprint 1. Sprint 4+ tasks are long-term improvements that can be prioritized based on needs.

---

## Sprint Plan for Execution Module (Phase 5)

**Sprint 1 (Immediate):** **COMPLETE (2025-10-11, ~12 hours actual)**
- Task 27: Directory reorganization ✓
- Task 28: README.md documentation fix ✓
- Task 29: TokenManager refactoring (Part 1) ✓

**Sprint 2-3 (Short-term - 4-6 hours remaining):**
Priority: HIGH/MEDIUM
- Task 30: Complete TokenManager refactoring ✓ COMPLETE (2025-10-11, ARCHIVED)
- Task 31: Implement ExecutionRuleRegistry ✓ COMPLETE (2025-10-11, ~6 hours actual)
- Task 32: Unify state tracking ✓ COMPLETE (2025-10-11, ~4 hours actual)
- Task 33: Expand ExecutionContext protocol (NEXT - final Sprint 2-3 task)

**Sprint 4+ (Long-term - 25-34 hours):**
Priority: MEDIUM/LOW
- Task 34: Domain events system
- Task 35: Type discipline improvements
- Task 36: EnvelopeFactory modernization
- Task 37: Performance optimizations

**Phase 4 (Optional - 13-18 hours):**
Priority: LOW
- Tasks 18-22: Diagram module optional improvements

---

**Last updated:** 2025-10-11
**Next review:** After Sprint 2-3 completion
