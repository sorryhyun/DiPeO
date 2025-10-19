# DiPeO Project Todos

## Fix Background Execution Timeout State Bug (High Priority) - IN PROGRESS

**Goal**: Properly update execution state when background executions timeout

**Context**: Discovered that when `dipeo run --background` times out, the background process is killed but the state store is never updated. Executions remain in "running" state forever, creating zombie states.

**Target**: Background executions that timeout should have their state updated to "failed" with timeout error information

**Root Cause Identified**:
- `MetricsObserver` was responsible for persisting execution state, but only subscribed to metrics-related events
- `EXECUTION_ERROR` events (including timeouts) were published to `message_router` but not `event_bus`, so observers never saw them
- `update_status()` deliberately doesn't persist final states (COMPLETED, FAILED, ABORTED) to avoid race conditions with MetricsObserver

**Solution Implemented**:
- ✅ Created `ResultObserver` with single responsibility: persist execution state changes
- ✅ Registered `ResultObserver` in `cli_runner.py` to subscribe to EXECUTION_STARTED, EXECUTION_COMPLETED, EXECUTION_ERROR
- ✅ Updated timeout handling to publish `EXECUTION_ERROR` to both `message_router` AND `event_bus`

**Progress Summary**:
- ✅ **Root cause identified**: Multiple issues including events not reaching observers, timeout handler only checking RUNNING state, EventForwarder overwriting status
- ✅ **ResultObserver implemented**: Successfully persists FAILED status to database with proper error messages
- ✅ **WAL checkpoint added**: Database writes complete successfully with verification
- ⚠️ **External reader issue discovered**: Internal verification shows correct data, but external processes see stale state

**Current Blocker**:
- **Symptom**: External processes (`dipeo results`, `sqlite3` CLI) read stale "running" status
- **Confirmed working**: Internal verification query shows correct `('failed', 'Execution timed out after 1 seconds')`
- **Confirmed working**: WAL checkpoint completes successfully: `(0, 7, 7)` - 7 pages checkpointed
- **Root cause unknown**: WAL isolation, connection pooling, or checkpoint timing issue
- **Impact**: Timeout handling works internally but results aren't visible to other processes

### Remaining Task

- [ ] Debug external reader stale data issue (BLOCKED)
  - **Symptom**: `dipeo results` and `sqlite3` CLI both show "running" status
  - **Confirmed working**: Internal verification shows `('failed', 'Execution timed out after 1 seconds')`
  - **Confirmed working**: WAL checkpoint: `(0, 7, 7)` - 7 pages successfully checkpointed
  - **Investigation needed**:
    - Why do external processes see stale snapshot despite successful WAL checkpoint?
    - Possible causes: WAL reader isolation, database connection pooling, timing issues
    - Try: Force reader to open new connection, check WAL mode settings, test with TRUNCATE checkpoint
  - Estimated effort: Medium (2-3 hours)
  - Files: `dipeo/infrastructure/execution/state/persistence_manager.py`, `dipeo/infrastructure/execution/state/cache_first_state_store.py`
  - Risk: Medium - may require WAL mode changes or connection pool adjustments

---

**Summary**:
- **Completed**: 7/7 core tasks - timeout detection, event publishing, observer creation, WAL checkpointing all working
- **Remaining**: 1 task - external process isolation issue (internal writes verified correct)
- **Effort remaining**: 2-3 hours
- **Status**: Core functionality works, but external readers need investigation

---

## Improve Async Execution Results Output (Medium Priority)

**Goal**: Enhance `dipeo results` command to show meaningful execution outputs and conversation history

**Context**: Currently `dipeo results` shows basic status info (executed_nodes, status, LLM usage) but doesn't show the actual messages/interactions that occurred during execution. Users need to see what was actually done, not just metadata.

**Target**: Rich output showing conversation history, node outputs with actual content, and final results

### Tasks

- [ ] Enhance `dipeo results` output to include conversation history
  - Extract and format messages from executed person_job nodes
  - Show user prompts and assistant responses
  - Include timestamps for each interaction
  - Estimated effort: Small (1-2 hours)
  - Files: `apps/server/src/dipeo_server/cli/cli_runner.py`
  - Risk: Low - read-only enhancement

- [ ] Include actual node output content in results
  - Currently showing `node_outputs` as stringified objects
  - Parse and extract meaningful content from envelopes
  - Show final output content (e.g., from endpoint nodes)
  - Estimated effort: Small (1 hour)
  - Files: `apps/server/src/dipeo_server/cli/cli_runner.py`
  - Risk: Low - formatting improvement

- [ ] Add `--verbose` flag for detailed output
  - Default: Show summary with final results and key messages
  - Verbose: Show full conversation history, all node outputs, metadata
  - Estimated effort: Small (30 min)
  - Files: `apps/server/src/dipeo_server/cli/entry_point.py`
  - Risk: Low - optional flag

- [ ] Update MCP `see_result` to return rich output
  - Include conversation history in MCP tool response
  - Format for easy consumption by LLM clients
  - Estimated effort: Small (30 min)
  - Files: `apps/server/src/dipeo_server/api/mcp_sdk_server.py`
  - Risk: Low - backward compatible addition

---

**Total estimated effort**: 3-4 hours
**Total tasks**: 4 tasks
**Risk**: Low - all enhancements are additive and don't break existing functionality

---

## Recently Completed

### CLI Background Execution & MCP Simplification ✅
**Completed**: 2025-10-19
**Total effort**: ~10 hours (13 tasks across 4 phases)

**Achievements**:
- ✅ Added native background execution support to DiPeO CLI
- ✅ Implemented `dipeo run --background` command with subprocess isolation
- ✅ Implemented `dipeo results <session_id>` command for async result retrieval
- ✅ Simplified MCP server to use CLI commands (removed complex execution matching)
- ✅ Cleaned up mcp_utils.py (removed execution_id parameter)
- ✅ Fully tested CLI and MCP async execution workflow
- ✅ Updated documentation (MCP integration guide + CLAUDE.md)

**Key benefits delivered**:
1. **Clean separation**: CLI owns execution, MCP just calls it
2. **Reusable**: Background execution available to all CLI users, not just MCP
3. **Simpler**: No complex execution matching heuristics
4. **Testable**: Can test background execution without server
5. **Maintainable**: Single source of truth for execution tracking

**Files modified**:
- `apps/server/src/dipeo_server/cli/cli_runner.py` - Added execution_id parameter and show_results method
- `apps/server/src/dipeo_server/cli/entry_point.py` - Added --background flag and results command
- `apps/server/src/dipeo_server/api/mcp_sdk_server.py` - Simplified run_backend and see_result to use CLI
- `apps/server/src/dipeo_server/api/mcp_utils.py` - Removed execution_id parameter
- `docs/features/mcp-server-integration.md` - Added async execution documentation
- `CLAUDE.md` - Added async CLI commands section

---

_Use `/dipeotodos` to view this file anytime._
