# DiPeO Frontend Refactoring - Current Issues and Solutions

## Summary of Refactoring (Phase 1-4 Completed)

Following the TODO.md plan, the frontend has been refactored through Phase 4 to establish clear module boundaries and eliminate cross-slice violations. However, some critical issues remain that need to be addressed.

## Last Updated: 2025-07-08 (Session 3)

## Fixed Issues (Updated 2025-07-08)

### Session 1 Fixes:
1. **Import Violation in importExportHelpers.ts** ✅
   - Removed direct import of feature layer code from core layer
   - Made `createNode` accept node configuration as parameters instead of importing from features

2. **Cross-slice Violation in PersonSlice** ✅
   - Removed `dataVersion` increments from PersonSlice since it belongs to DiagramSlice
   - PersonSlice now only manages person-related state

3. **Improved Store Architecture** ✅
   - Added proper clear/restore methods to each slice
   - Refactored `clearAll` and `restoreSnapshot` to use slice methods

4. **TypeScript Errors** ✅
   - Fixed `createNode` function signature mismatch in importExportHelpers.ts
   - Added missing HandleID import in unifiedStore.ts
   - Added timestamp property to snapshot in useDiagramLoader.ts
   - Updated UnifiedStore types to include cleanupNodeHandles method

5. **Handle Cleanup System** ✅
   - Added `cleanupNodeHandles` method to UnifiedStore
   - Updated DiagramSlice deleteNode and batchDeleteNodes to use the new method
   - This prevents cross-slice violations when deleting nodes

### Session 2 Fixes:
6. **WeakMap Error in computedGetters.ts** ✅
   - Fixed "Invalid value used as weak map key" error
   - Replaced WeakMap with a simple cache object to avoid initialization issues
   - Added proper null checks for store and Map instances
   - Added try-catch error handling in getter functions

### Session 3 Fixes:
7. **Diagram Not Rendering Issue** ✅
   - Fixed the computed arrays (nodesArray, arrowsArray, personsArray) not being populated
   - Root cause: Getter properties don't work with Zustand's immer middleware
   - Solution: Converted getter properties to regular state properties maintained in slices
   - Updated afterChange in diagramSlice to update arrays when Maps change
   - Updated personSlice to update personsArray when persons Map changes
   - Updated all snapshot restore operations to also update arrays
   - Result: Diagram now renders correctly with all nodes and edges visible

## Remaining Issues

### 1. ~~Diagram Not Rendering (CRITICAL)~~ - FIXED ✅
**Problem**: Diagram data loads successfully (nodes: Map(7), arrows: Map(8)) but the canvas remains empty. User cannot drag nodes to canvas.

**Current Status**:
- Data is loaded into the store correctly (Maps are populated)
- The UI components (sidebar, controls) render properly
- React Flow canvas appears but shows no nodes/edges
- ✅ WeakMap error fixed in computedGetters.ts

**Root Cause Analysis (Session 2 Findings)**:
- ✅ Fixed WeakMap initialization error
- ❌ **Critical Issue Found**: `nodesArray` is empty despite `nodes` Map having 7 items
- The computed arrays (nodesArray, arrowsArray, personsArray) are not being generated from the Maps
- Console logs show:
  ```
  [useCanvas] Converting nodes to React Flow format: {
    nodesArrayLength: 0,    // Should be 7!
    handlesByNodeSize: 7,   // Handles are loaded correctly
    nodesArray: Array(0)    // Empty array!
  }
  ```
- The issue appears to be in the computed getters or the relationship between Maps and Arrays

**Debugging Progress**:
1. Added debug logging to useCanvas hook - confirmed nodesArray is empty
2. Added debug logging to DiagramCanvas - confirmed it receives empty arrays
3. Fixed WeakMap error in computedGetters.ts
4. Issue persists: computed arrays are not being populated from Maps

**Next Steps**:
1. Debug why `nodesArray` getter is returning empty array when `nodes` Map has data
2. Check if the dataVersion is triggering array regeneration properly
3. Verify the computed getters are being called at the right time
4. Check if there's a race condition between Map population and array generation

### 2. Cross-Slice Violations (Partially Fixed)
**Problem**: Some cross-slice violations still occur during diagram operations.

**Current Status**:
- ✅ Fixed violations in node deletion by adding cleanupNodeHandles method
- ⚠️  Still seeing violations when restoring diagram due to history tracking
- The logger shows violations when modifying properties from multiple slices

**Solution Implemented**:
- Added `cleanupNodeHandles` method to UnifiedStore
- Updated DiagramSlice to use this method instead of direct handle manipulation
- Simplified restoreSnapshot to avoid complex transactions

### 3. Handle Management Architecture
**Status**: ✅ RESOLVED
- Created dedicated `cleanupNodeHandles` method in UnifiedStore
- DiagramSlice now calls this method when deleting nodes
- Prevents orphaned handles and maintains clean separation of concerns

## Immediate Action Items

1. **Debug Diagram Rendering** (PRIORITY)
   - Add console logging to useCanvas hook to verify node/edge conversion
   - Check DiagramAdapter.nodeToReactFlow and arrowToReactFlow conversions
   - Verify React Flow is receiving proper node/edge data structures
   - Check if handles are being created and indexed before nodes are converted
   - Add logging to DiagramCanvas to see what props React Flow receives

2. **Fix Remaining Cross-Slice Violations**
   - Consider moving history tracking out of individual slice updates
   - Implement a cleaner transaction system that respects slice boundaries
   - Review all places where multiple slices are updated simultaneously

3. **Performance Optimization**
   - The computed arrays (nodesArray, arrowsArray) use memoization
   - Verify the dataVersion is incrementing properly to trigger re-renders
   - Check if React Flow is properly responding to data changes

## Long-term Improvements

1. **Consider Unified Handle Management**
   - Handles are tightly coupled with nodes, so they might belong in DiagramSlice
   - This would eliminate cross-slice violations and simplify the architecture

2. **Improve Transaction System**
   - Current transaction system doesn't prevent cross-slice violations
   - Consider implementing a more robust transaction mechanism that enforces slice boundaries

3. **Add Integration Tests**
   - Test diagram loading/saving flow
   - Test node deletion with handle cleanup
   - Test cross-slice update detection

## Testing Checklist

- [x] TypeScript compilation passes without errors
- [x] Diagram loads without console errors (WeakMap error fixed)
- [ ] No cross-slice violation warnings in console (partially fixed)
- [x] Nodes and connections render properly (FIXED - diagram renders correctly)
- [x] Node deletion cleans up handles (implemented cleanupNodeHandles)
- [x] Diagram can be saved and reloaded (works via quicksave)
- [x] Performance is acceptable with large diagrams
- [x] User can drag nodes from palette to canvas (verified working)

## Summary of Progress

### Session 1 (2025-07-08):
1. **Fixed TypeScript Errors**: All type checking errors resolved
2. **Implemented Handle Cleanup**: Added proper handle cleanup system to prevent cross-slice violations
3. **Fixed Immer Errors**: Resolved frozen object mutations in restoreSnapshot
4. **Identified Critical Issue**: Diagram data loads but doesn't render

### Session 2 (2025-07-08):
1. **Fixed WeakMap Error**: Resolved "Invalid value used as weak map key" error in computedGetters.ts
2. **Diagnosed Rendering Issue**: Found that computed arrays (nodesArray, arrowsArray) are empty despite Maps being populated
3. **Added Debug Logging**: Instrumented useCanvas and DiagramCanvas to trace data flow
4. **Identified Root Cause**: The computed getters are not properly converting Maps to Arrays

## Critical Issue Summary

The main issue preventing diagram rendering is that the computed arrays used by React Flow are empty:
- `nodes` Map has 7 items ✓
- `nodesArray` computed getter returns empty array ✗
- `handles` are properly indexed ✓
- React Flow receives empty nodes array ✗

This is a fundamental issue in the store's computed getters that needs to be resolved before the diagram can render properly.