# DiPeO Project Todos

## Frontend Improvements (2025-10-08)

### Critical Priority - Foundation (Do First)
**These establish core infrastructure needed for all other work**

- [ ] **Fix type safety in store** (2025-10-08)
  - Replace `any` with proper Zustand types in store slices
  - Effort: Medium
  - Impact: High - Enables better type checking across app
  - Dependency: Should be done before component refactoring

- [ ] **Configure GraphQL scalars** (2025-10-08)
  - Update codegen.yml with `DateTime: string`, `JSON: Record<string, unknown>`
  - Effort: Small
  - Impact: High - Fixes type generation issues
  - Dependency: Required before GraphQL error handling UI

- [ ] **Add error boundaries** (2025-10-08)
  - Wrap main components: DiagramCanvas, ConversationDashboard
  - Effort: Small
  - Impact: Critical - Prevents app crashes
  - Parallel: Can do independently

- [ ] **Create logger utility** (2025-10-08)
  - Replace 156 console.* calls with production-safe logger
  - Effort: Medium
  - Impact: High - Essential for debugging and monitoring
  - Parallel: Can do independently, applies to all future work

---

### High Priority - Type Safety & Validation
**Improves code quality and catches errors early**

- [ ] **Enable TypeScript strict mode** (2025-10-08)
  - Gradually enable stricter compiler options
  - Effort: Large
  - Impact: High - Catches more bugs at compile time
  - Dependency: Best done after store type safety (#1) is fixed
  - Notes: Do incrementally, file by file or feature by feature

- [ ] **Centralize validation logic** (2025-10-08)
  - Consolidate duplicate validation across validation-service and validators.ts
  - Effort: Medium
  - Impact: Medium - Reduces bugs, easier maintenance
  - Parallel: Can do independently

---

### High Priority - Performance Optimization
**Improves runtime performance and user experience**

- [ ] **Fix array sync performance** (2025-10-08)
  - Replace afterChange array sync with computed selectors
  - Effort: Medium
  - Impact: High - Reduces unnecessary re-renders
  - Parallel: Can do independently

- [ ] **Optimize ReactFlow props** (2025-10-08)
  - Extract stable callbacks with useEvent in useCommonFlowProps
  - Effort: Small
  - Impact: Medium - Prevents unnecessary ReactFlow re-renders
  - Parallel: Can do independently

- [ ] **Optimize CanvasContext** (2025-10-08)
  - Split into: CanvasStateContext, CanvasOperationsContext, CanvasSelectionContext
  - Effort: Medium
  - Impact: High - Reduces context re-render overhead
  - Parallel: Can do independently

- [ ] **Optimize GraphQL cache** (2025-10-08)
  - Add optimistic updates and smart merge strategies
  - Effort: Large
  - Impact: Medium - Improves perceived performance
  - Dependency: Better done after GraphQL scalars are configured (#2)

---

### High Priority - Component Refactoring
**Large components that need breaking down (Can be done in parallel)**

- [ ] **Split BaseNode.tsx** (2025-10-08)
  - Break down 538-line component into:
    - NodeContainer (wrapper, styling, selection)
    - NodeHandles (input/output handles)
    - NodeFlipControls (flip button)
  - Effort: Large
  - Impact: High - Easier maintenance and testing
  - Parallel: Can do independently

- [ ] **Split UnifiedFormField.tsx** (2025-10-08)
  - Break down 562-line component into focused field components:
    - TextFormField
    - NumberFormField
    - SelectFormField
    - MultiSelectFormField
    - etc.
  - Effort: Large
  - Impact: High - Easier to maintain and test
  - Parallel: Can do independently

- [ ] **Split ConversationDashboard.tsx** (2025-10-08)
  - Break down 483-line component into sub-components:
    - ConversationList
    - ConversationHeader
    - MessageThread
    - MessageInput
  - Effort: Large
  - Impact: High - Better code organization
  - Parallel: Can do independently

---

### Medium Priority - Code Quality & Standards
**Improves maintainability and consistency**

- [ ] **Extract magic numbers to constants** (2025-10-08)
  - Create CANVAS_CONSTANTS for sizing, spacing, scale factors
  - Effort: Small
  - Impact: Low - Better maintainability
  - Parallel: Can do independently

- [ ] **Implement or track TODOs** (2025-10-08)
  - Address 9 TODO/FIXME comments or create GitHub issues
  - Effort: Medium (depends on individual TODOs)
  - Impact: Medium - Reduces technical debt
  - Parallel: Can do independently

- [ ] **Standardize event handler naming** (2025-10-08)
  - Use handleX for local handlers, onX for props
  - Effort: Medium
  - Impact: Low - Better code consistency
  - Parallel: Can do independently

---

### Medium Priority - User Experience
**Improves user-facing features**

- [ ] **Add GraphQL error handling UI** (2025-10-08)
  - Create consistent error toast/display for GraphQL errors
  - Effort: Medium
  - Impact: Medium - Better user feedback
  - Dependency: Should be done after GraphQL scalars (#2)

- [ ] **Add accessibility attributes** (2025-10-08)
  - Add ARIA labels to interactive elements
  - Effort: Large (touches many components)
  - Impact: Medium - Improves accessibility
  - Parallel: Can do independently

---

### Medium Priority - DevOps & Monitoring
**Improves development workflow**

- [ ] **Add bundle size monitoring** (2025-10-08)
  - Set up bundle analysis in build process
  - Effort: Small
  - Impact: Low - Helps track bundle growth
  - Parallel: Can do independently

---

## Completed (2025-10-05)

### Metrics Tracking System Enhancement
All metrics tracking implementation tasks have been completed:
- ✅ Modified service.py to track API calls hierarchically using phase names like "memory_selection__api_call"
- ✅ Updated display.py to aggregate and display hierarchical phases with nested timing structure and overhead calculation
- ✅ Enhanced metrics_observer.py to preserve hierarchical phase names
- ✅ Tested implementation with simple_iter diagram
- ✅ Verified metrics breakdown output shows correct hierarchical display

**Impact**: The metrics system now correctly displays hierarchical timing structure, showing API calls within their execution context (memory_selection vs completion), accurate call counts, and overhead calculations for optimization targeting.

---

## Future Optimization Opportunities

Based on the enhanced metrics system, potential optimization areas:

1. **Memory Selection Preprocessing** (if metrics reveal slowness):
   - Reduce MEMORY_HARD_CAP (150 → 50-75)
   - More aggressive pre-filtering
   - Cache scoring results

2. **Prompt Building Optimization**:
   - Reduce snippet lengths
   - Simplify selection prompt
   - Cache prompt templates

3. **Parallel Processing**:
   - Verify nodes execute in parallel
   - Check if memory selection blocks parallelization
