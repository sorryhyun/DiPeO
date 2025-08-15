# Goal

Enable a **multi‑run monitor board** in the browser where **multiple diagram executions render side‑by‑side horizontally**. Each run shows a live, read‑only diagram with highlights, status, logs, and controls (pause/abort).

---

## UX Overview

- New **Monitor Board** view: horizontally arranged columns (one column per execution).
- Columns are **snap‑scrollable** with mouse wheel + shift, trackpad, or drag on scrollbar.
- Each column header: run name, status chip, elapsed time, node counters, pause/abort.
- Add/Remove runs at runtime; reorder via drag handle.
- Optional compact mode (mini map + active nodes list only).

**Routing**

- New route: `/monitor/board` (or `?monitor=board&ids=exec1,exec2`).
- Deep‑linkable: copying the URL preserves which runs are on the board.

---

## Architecture Options

### A) "Many subscriptions, one per column" (MVP)

- Keep current `execution_updates(execution_id)` subscription.
- Each column component manages **its own** subscription and local state.
- Minimal backend change; fastest path.

### B) "One subscription, many execution IDs" (Scales better)

- Add `multi_execution_events(execution_ids: [ID!]!)` subscription.
- Server multiplexes events; client receives unified stream.
- Reduces socket overhead for 5–20 parallel runs.

We can **ship A first**, then add B for scale.

---

## State Model

### Option A (Local per‑column store)

- Each `RunColumn` owns a small Zustand store instance (context‑scoped) to avoid interfering with today’s global `execution` slice.
- The diagram canvas in the column reads from this local store.

```ts
// executionLocalStore.ts
import { createStore } from 'zustand/vanilla';
export type StoreExecutionState = {
  id: string | null;
  isRunning: boolean;
  runningNodes: Set<string>;
  nodeStates: Map<string, { status: string; timestamp: number; error?: string|null }>;
  startedAt: number | null;
  finishedAt: number | null;
};
export const createExecutionLocalStore = () => createStore<StoreExecutionState>(() => ({
  id: null, isRunning: false, runningNodes: new Set(), nodeStates: new Map(), startedAt: null, finishedAt: null,
}));
```

We wrap each column with a provider exposing this store to `DiagramCanvas` via props or context.

### Option B (Global multi‑map)

- Extend unified store (`executionsById: Record<ExecutionID, StoreExecutionState>`).
- `DiagramCanvas` gains `executionId` prop to select which execution slice to read.
- Larger refactor; keeps all state centralized.

**Recommendation**: Start with **Option A** (no breaking changes), add B later if we need global cross‑run operations.

---

## Frontend Components

```
/apps/web/src/ui/components/monitor-board/
  ExecutionBoardView.tsx     # Top-level page (grid + toolbar)
  RunColumn.tsx              # One execution column (header + DiagramCanvas + logs)
  RunPicker.tsx              # Add runs to board (search + recent)
  useMultiRunSubscriptions.ts # Hook for option B (multi-id subscription)
```

### ExecutionBoardView (horizontal layout)

```tsx
export default function ExecutionBoardView() {
  const [executionIds, setExecutionIds] = useUrlSyncedIds(); // ids from query string
  return (
    <div className="h-full flex flex-col bg-gray-900">
      <BoardToolbar executionIds={executionIds} onAdd={id=>addId(id)} onRemove={removeId} />
      <div
        className="flex-1 overflow-x-auto overflow-y-hidden"
        style={{ scrollSnapType: 'x mandatory' }}
      >
        <div
          className="min-h-full grid gap-4 px-4 py-2"
          style={{ gridAutoFlow: 'column', gridAutoColumns: 'minmax(480px, 1fr)' }}
        >
          {executionIds.map(id => (
            <RunColumn key={id} executionId={id} />
          ))}
        </div>
      </div>
    </div>
  );
}
```

### RunColumn (one run)

```tsx
function RunColumn({ executionId }: { executionId: string }) {
  const store = useMemo(() => createExecutionLocalStore(), []);
  useRunSubscription({ executionId, store }); // wires GraphQL → store

  return (
    <div className="rounded-2xl bg-gray-800/60 border border-gray-700 shadow p-3" style={{ scrollSnapAlign: 'start' }}>
      <RunHeader executionId={executionId} store={store} />
      <div className="h-[56vh] rounded-xl overflow-hidden mb-3">
        <DiagramCanvas executionMode store={store} readOnly />
      </div>
      <EventStrip executionId={executionId} store={store} />
    </div>
  );
}
```

### Hook: per‑column subscription (Option A)

```ts
import { useEffect } from 'react';
import { useApolloClient } from '@apollo/client';
import { ExecutionUpdatesDocument } from '@/__generated__/graphql';

export function useRunSubscription({ executionId, store }) {
  const client = useApolloClient();
  useEffect(() => {
    if (!executionId) return;
    const sub = client.subscribe({
      query: ExecutionUpdatesDocument,
      variables: { execution_id: executionId },
    }).subscribe({
      next: ({ data }) => applyExecutionUpdate(store, data.execution_updates),
      error: (e) => console.error('[Board] subscription error', e),
    });
    return () => sub.unsubscribe();
  }, [executionId]);
}
```

### DiagramCanvas changes

- Add optional `store` prop to read node highlights/state from the **local run store** instead of the unified store.
- Keep existing behavior when `store` is not provided (backward compatible).

```tsx
<DiagramCanvas executionMode store={store} readOnly />
```

### Styling & Performance

- Use CSS Grid + `grid-auto-flow: column` and `grid-auto-columns: minmax(480px,1fr)`.
- `scroll-snap-type: x mandatory;` and `scrollSnapAlign: 'start'` for pleasant horizontal paging.
- Virtualize event lists per column (e.g., `react-window`) and throttle UI updates via `requestAnimationFrame` or 100–200ms debounced setState.
- **IntersectionObserver**: pause off‑screen column updates (keep subscription, but batch renders).

---

## Backend (Option B) — Multi‑ID Subscription

Add a new subscription that accepts multiple execution IDs and emits any event belonging to those IDs.

```py
# apps/server/.../schema/subscriptions.py
@strawberry.subscription
async def multi_execution_events(self, execution_ids: list[strawberry.ID]) -> AsyncGenerator[JSONScalar, None]:
    message_router = registry.get(MESSAGE_ROUTER)
    event_queue = asyncio.Queue()
    connection_id = f"graphql-multi-{id(event_queue)}"

    async def handler(message):
        await event_queue.put(serialize_for_json(message))

    await message_router.register_connection(connection_id, handler)
    try:
        # subscribe to each execution
        for ex in execution_ids:
            await message_router.subscribe_connection_to_execution(connection_id, str(ex))
        while True:
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                yield event  # client filters if needed
            except asyncio.TimeoutError:
                continue
    finally:
        for ex in execution_ids:
            await message_router.unsubscribe_connection_from_execution(connection_id, str(ex))
        await message_router.unregister_connection(connection_id)
```

**Frontend query generator**: add

```py
# files/codegen/code/frontend/queries/executions_queries.py
queries.append("""
subscription MultiExecutionEvents($executionIds: [ID!]!) {
  multi_execution_events(execution_ids: $executionIds)
}
""")
```

Then regenerate:

```
dipeo run codegen/diagrams/generate_all --light --debug
make apply-syntax-only
make graphql-schema
```

**Client hook** (Option B):

```ts
export function useMultiRunSubscriptions(ids: string[], onEvent: (e: any)=>void) {
  const { data } = useMultiExecutionEventsSubscription({ executionIds: ids }, { skip: !ids.length });
  useEffect(() => { if (data?.multi_execution_events) onEvent(data.multi_execution_events); }, [data]);
}
```

---

## URL & TopBar Integration

- Interpret `?monitor=board` to activate the board and switch `activeCanvas` to `'monitor'`.
- Parse `ids` query param to pre‑load columns; expose a UI **RunPicker** to add/remove IDs without hand‑editing the URL.
- For backward compatibility, `?monitor=true` continues to open the **single‑run** view.

---

## Logs & Mini‑widgets

- `EventStrip` shows a condensed timeline (EXECUTION\_STARTED, NODE\_COMPLETED, WARN/ERROR).
- Hover to see tooltips; click to scroll the canvas to a node.
- Optional **Mini Metrics** per column: duration, throughput, #errors, token usage.

---

## QA Checklist

-

---

## Phased Rollout

1. **MVP** (Option A): per‑column subscriptions + local stores + grid layout.
2. **Scale** (Option B): server multi‑ID subscription + single client stream.
3. **Refactor**: optional global multi‑execution slice if cross‑run analytics are needed.

---

## Developer Notes

- Keep DiagramCanvas strictly **read‑only** in board mode (no edits, only highlights).
- Throttle high‑frequency updates (node state changes) and prefer idempotent reducers in stores.
- Use `requestIdleCallback` for non‑critical board layout recalculations after column add/remove.

