# Monitor UI Cleanup Analysis

## Executive Summary

The DiPeO frontend has TWO separate monitoring implementations:
1. **Monitor Mode** (`?monitor=true`) - ACTIVE and DOCUMENTED
2. **Monitor Board** (`?monitor=board`) - UNUSED and UNDOCUMENTED

## Investigation Findings

### 1. Monitor Mode (?monitor=true) - KEEP THIS

**Status:** ACTIVE, DOCUMENTED, USED

**Entry Point:** `/apps/web/src/domain/execution/hooks/useMonitorMode.ts`

**Components:**
- `ExecutionView` - Main execution view container
- `ExecutionControls` - Control bar with run/stop/pause buttons
- `DiagramCanvas` (executionMode=true) - Diagram with execution highlighting
- `ConversationTab` - Bottom panel with tabbed interface
  - **Tab 1: Conversation** - `ConversationDashboard` component
  - **Tab 2: Execution Order** - `ExecutionOrderView` component
  - **Tab 3: Execution Log** - `ExecutionLogView` component
  - **Tab 4: Metrics** - `ExecutionMetricsView` component

**Documentation References:**
- CLAUDE.md: Line 119
- AGENTS.md: Line 119
- docs/agents/frontend-development.md: Line 81
- docs/integrations/claude-code.md: Line 408
- docs/architecture/graphql-subscriptions.md: Line 269
- .claude/agents/dipeo-frontend-dev.md: Line 22

**Usage:** Used by all developers for monitoring CLI-launched executions

### 2. Monitor Board (?monitor=board) - REMOVE THIS

**Status:** UNUSED, UNDOCUMENTED, POTENTIALLY EXPERIMENTAL

**Entry Point:** `/apps/web/src/ui/components/monitor-board/useMonitorBoardMode.ts`

**Components:**
```
/apps/web/src/ui/components/monitor-board/
├── ExecutionBoardView.tsx         - Main board view (multi-execution grid)
├── RunColumn.tsx                  - Individual execution column
├── RunHeader.tsx                  - Execution header with controls
├── EventStrip.tsx                 - Timeline of events
├── DiagramViewer.tsx              - Read-only diagram viewer
├── RunPicker.tsx                  - Modal for selecting executions
├── useAutoFetchExecutions.ts      - Auto-fetch active executions
├── useUrlSyncedIds.ts             - URL parameter synchronization
├── useRunSubscription.ts          - GraphQL subscription for execution updates
├── executionLocalStore.ts         - Local Zustand store for board state
├── useMonitorBoardMode.ts         - Hook for board mode detection
└── index.ts                       - Barrel export
```

**References Found:**
- Only referenced in `MainLayout.tsx` (conditional rendering)
- NO documentation
- NO tests
- NO examples
- NO usage in any documentation

**Conclusion:** Monitor board appears to be an experimental/abandoned feature for viewing multiple executions side-by-side. It was likely created as an alternative to the main monitor mode but never completed or adopted.

## Cross-Dependency Analysis

### Dependencies INTO monitor-board (External → monitor-board)
- `MainLayout.tsx` imports and conditionally renders `ExecutionBoardView`
- `MainLayout.tsx` uses `useMonitorBoardMode` hook

### Dependencies OUT OF monitor-board (monitor-board → External)
- Uses GraphQL hooks from `@/__generated__/graphql`
- Uses Zustand store utilities
- Uses Lucide React icons
- NO dependencies on main monitor mode components
- NO shared code between monitor mode and monitor board

**Result:** Monitor board is completely isolated from monitor mode. Removal is safe.

## Components to KEEP (Monitor Mode)

### UI Components:
1. `/apps/web/src/ui/components/execution/ExecutionView.tsx`
2. `/apps/web/src/ui/components/execution/ExecutionControls.tsx`
3. `/apps/web/src/ui/components/conversation/ConversationTab.tsx`
4. `/apps/web/src/ui/components/conversation/ConversationDashboard/ConversationDashboard.tsx`
5. `/apps/web/src/ui/components/execution/ExecutionOrderView/ExecutionOrderView.tsx`
6. `/apps/web/src/ui/components/execution/ExecutionLogView/ExecutionLogView.tsx`
7. `/apps/web/src/ui/components/execution/ExecutionMetricsView/ExecutionMetricsView.tsx`
8. `/apps/web/src/ui/components/execution/InteractivePromptModal.tsx`

### Hooks:
1. `/apps/web/src/domain/execution/hooks/useMonitorMode.ts`
2. `/apps/web/src/domain/execution/hooks/useExecution.ts`
3. `/apps/web/src/domain/execution/hooks/useExecutionState.ts`
4. `/apps/web/src/domain/execution/hooks/useExecutionStreaming.ts`
5. `/apps/web/src/domain/execution/hooks/useExecutionLogStream.ts`
6. `/apps/web/src/domain/execution/hooks/useExecutionMetrics.ts`
7. `/apps/web/src/domain/execution/hooks/useConversationData.ts`

## Components to REMOVE (Monitor Board)

### Entire Directory:
```
/apps/web/src/ui/components/monitor-board/
```

### Imports to Update:
1. `/apps/web/src/ui/layouts/MainLayout.tsx`
   - Remove: `import { useMonitorBoardMode } from '../components/monitor-board/useMonitorBoardMode'`
   - Remove: `const LazyExecutionBoardView = React.lazy(...)`
   - Remove: `const { isMonitorBoard, isSingleMonitor } = useMonitorBoardMode()`
   - Simplify: Conditional rendering logic

## Removal Plan

### Phase 1: Prepare (No code changes)
1. Backup monitor-board directory
2. Document removal in changelog
3. Notify team of upcoming removal

### Phase 2: Update MainLayout
1. Remove `useMonitorBoardMode` import and usage
2. Remove `LazyExecutionBoardView` import
3. Simplify conditional rendering (only check `activeCanvas`)
4. Test monitor mode still works

### Phase 3: Remove monitor-board Directory
1. Delete `/apps/web/src/ui/components/monitor-board/` directory
2. Run `pnpm typecheck` to ensure no broken imports
3. Test application builds successfully

### Phase 4: Verification
1. Test `?monitor=true` works correctly
2. Verify all 4 tabs are accessible
3. Test execution monitoring end-to-end
4. Confirm no console errors

## Risk Assessment

**Risk Level:** LOW

**Reasons:**
- Monitor board is not documented anywhere
- No cross-dependencies with main monitor mode
- Only one file (`MainLayout.tsx`) needs updating
- Monitor mode (`?monitor=true`) remains unchanged
- All useful tabs (conversation, execution order, log, metrics) are part of monitor mode

**Rollback Plan:**
If issues arise, restore monitor-board directory from git history and revert MainLayout changes.

## Estimated Effort

- Investigation: COMPLETE
- Code changes: 15 minutes
- Testing: 15 minutes
- Total: 30 minutes

## Next Steps

1. Get approval for removal
2. Execute Phase 2 (Update MainLayout)
3. Execute Phase 3 (Remove directory)
4. Execute Phase 4 (Verification)
5. Commit changes with descriptive message
6. Update this analysis as COMPLETE
