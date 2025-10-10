# DiPeO Project TODOs

## High Priority: Monitor Board Cleanup (2025-10-10)

**Context**: Frontend has TWO separate monitoring implementations. Monitor Mode (?monitor=true) is active and documented. Monitor Board (?monitor=board) is unused/experimental and should be removed.

**Analysis**: See /home/soryhyun/DiPeO/MONITOR_CLEANUP_ANALYSIS.md for full investigation

**Scope**: 12 files in /apps/web/src/ui/components/monitor-board/ + 1 file to update (MainLayout.tsx)

**Risk**: LOW - Monitor board is completely isolated, no cross-dependencies with Monitor Mode

**Estimated Total Effort**: 30-45 minutes

---

### Phase 1: Pre-Cleanup Verification
**Goal**: Ensure Monitor Mode works correctly BEFORE making any changes

- [ ] Start development environment (make dev-all)
  - Estimated effort: Small

- [ ] Test Monitor Mode baseline functionality
  - Visit http://localhost:3000/?monitor=true
  - Run test diagram: dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=40
  - Verify all 4 tabs work: Conversation, Execution Order, Execution Log, Metrics
  - Check for console errors in browser DevTools
  - Estimated effort: Small

- [ ] Document current working state
  - Take screenshots of working Monitor Mode (optional but recommended)
  - Note any existing issues/warnings in console
  - Estimated effort: Small

---

### Phase 2: Update MainLayout.tsx
**Goal**: Remove all references to monitor-board from MainLayout

- [ ] Backup monitor-board directory
  - Create git branch: git checkout -b cleanup/remove-monitor-board
  - Verify branch created: git branch
  - Estimated effort: Small

- [ ] Update MainLayout.tsx - Remove imports
  - File: /apps/web/src/ui/layouts/MainLayout.tsx
  - Remove: import { useMonitorBoardMode } from '../components/monitor-board/useMonitorBoardMode'
  - Remove: const LazyExecutionBoardView = React.lazy(...) import
  - Estimated effort: Small

- [ ] Update MainLayout.tsx - Remove hook usage
  - File: /apps/web/src/ui/layouts/MainLayout.tsx
  - Remove: const { isMonitorBoard, isSingleMonitor } = useMonitorBoardMode()
  - Estimated effort: Small

- [ ] Update MainLayout.tsx - Simplify conditional rendering
  - File: /apps/web/src/ui/layouts/MainLayout.tsx
  - Remove: ExecutionBoardView conditional rendering block
  - Simplify: Only check activeCanvas for rendering logic
  - Keep: ExecutionView rendering (this is Monitor Mode)
  - Estimated effort: Medium

- [ ] Run TypeScript type checking
  - Command: cd apps/web && pnpm typecheck
  - Verify: No new type errors introduced
  - Estimated effort: Small

---

### Phase 3: Remove monitor-board Directory
**Goal**: Delete all unused monitor-board code

- [ ] Delete monitor-board directory
  - Path: /apps/web/src/ui/components/monitor-board/
  - Files to be deleted (12 total):
    - ExecutionBoardView.tsx
    - RunColumn.tsx
    - RunHeader.tsx
    - EventStrip.tsx
    - DiagramViewer.tsx
    - RunPicker.tsx
    - useAutoFetchExecutions.ts
    - useUrlSyncedIds.ts
    - useRunSubscription.ts
    - executionLocalStore.ts
    - useMonitorBoardMode.ts
    - index.ts
  - Command: rm -rf /apps/web/src/ui/components/monitor-board/
  - Estimated effort: Small

- [ ] Verify no broken imports
  - Command: cd apps/web && pnpm typecheck
  - Expected: All type checks pass
  - Fix any unexpected import errors if found
  - Estimated effort: Small

- [ ] Test application builds successfully
  - Command: cd apps/web && pnpm build
  - Expected: Build completes without errors
  - Estimated effort: Medium

---

### Phase 4: Post-Cleanup Verification
**Goal**: Ensure Monitor Mode still works after cleanup

- [ ] Start development environment
  - Command: make dev-all (or make dev-server + make dev-web)
  - Verify both servers start without errors
  - Estimated effort: Small

- [ ] Test Monitor Mode functionality (same as Phase 1)
  - Visit http://localhost:3000/?monitor=true
  - Run test diagram: dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=40
  - Verify all 4 tabs work: Conversation, Execution Order, Execution Log, Metrics
  - Verify execution highlighting on diagram canvas
  - Check for console errors (should be none)
  - Estimated effort: Medium

- [ ] Test that ?monitor=board no longer renders anything
  - Visit http://localhost:3000/?monitor=board
  - Expected: Should render default view (not monitor board)
  - No console errors related to monitor board
  - Estimated effort: Small

- [ ] Run linter
  - Command: cd apps/web && pnpm lint
  - Fix any new linting issues
  - Estimated effort: Small

---

### Phase 5: Documentation & Commit
**Goal**: Document changes and commit cleanup

- [ ] Review git diff
  - Command: git diff
  - Verify only expected files changed:
    - Modified: apps/web/src/ui/layouts/MainLayout.tsx
    - Deleted: apps/web/src/ui/components/monitor-board/ (entire directory)
  - Estimated effort: Small

- [ ] Stage changes
  - Command: git add apps/web/src/ui/layouts/MainLayout.tsx
  - Command: git add apps/web/src/ui/components/monitor-board/
  - Estimated effort: Small

- [ ] Create commit
  - Message format:
    ```
    feat(web): remove unused monitor board implementation

    Remove experimental/abandoned monitor board (?monitor=board) feature.
    Keep active Monitor Mode (?monitor=true) unchanged.

    Changes:
    - Delete /apps/web/src/ui/components/monitor-board/ (12 files)
    - Update MainLayout.tsx to remove monitor board references
    - Simplify conditional rendering logic in MainLayout

    Risk: Low - monitor board was unused and undocumented
    Impact: None - Monitor Mode functionality preserved

    See MONITOR_CLEANUP_ANALYSIS.md for full investigation
    ```
  - Estimated effort: Small

- [ ] Update MONITOR_CLEANUP_ANALYSIS.md
  - Add completion note at top of document
  - Mark status as COMPLETE with date
  - List actual changes made
  - Estimated effort: Small

- [ ] Optional: Update CHANGELOG or release notes
  - Note removal of experimental monitor board feature
  - Clarify that Monitor Mode (?monitor=true) remains active
  - Estimated effort: Small

---

### Rollback Plan (If Issues Arise)

If Monitor Mode breaks or unexpected issues occur:

1. **Immediate rollback**:
   - Command: git checkout dev (or main branch)
   - Command: git branch -D cleanup/remove-monitor-board
   - Restore working state immediately

2. **Partial rollback** (if only MainLayout changes cause issues):
   - Command: git checkout HEAD -- apps/web/src/ui/layouts/MainLayout.tsx
   - Keep monitor-board deletion, revert MainLayout changes
   - Re-investigate MainLayout conditional logic

3. **Full restoration from git history**:
   - Command: git checkout <previous-commit-hash> -- apps/web/src/ui/components/monitor-board/
   - Restore entire monitor-board directory if needed

---

## Backlog

### Future Enhancements (Post-Cleanup)
- [ ] Consider adding E2E tests for Monitor Mode to prevent regressions
- [ ] Review other potential dead code in frontend (low priority)
- [ ] Document Monitor Mode architecture in /docs/architecture/ (if not already documented)

---

**Task Breakdown Summary**:
- Phase 1 (Verification): 3 tasks - 10 min
- Phase 2 (MainLayout): 5 tasks - 15 min
- Phase 3 (Delete): 3 tasks - 10 min
- Phase 4 (Verification): 5 tasks - 15 min
- Phase 5 (Documentation): 5 tasks - 10 min
- **Total**: 21 tasks - 60 min (padded from original 30 min estimate for thoroughness)

**Last Updated**: 2025-10-10
**Status**: Ready to execute cleanup
**Analysis Document**: /home/soryhyun/DiPeO/MONITOR_CLEANUP_ANALYSIS.md
