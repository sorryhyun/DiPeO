# DiPeO TODO

## Module-Level Timing Metrics Implementation

### Overview
Add detailed module-level performance profiling using:
1. **In-process TimingCollector** - Zero-overhead metric collection (no log parsing)
2. **Decorators & Context Managers** - Clean syntax for automatic timing with exception safety
3. **Custom TIMING log level** - Optional structured logs for human debugging

**Quick Example**:
```python
# Decorator - time entire function
@atimed("memory_selection")
async def select_memories(self, execution_id, node_id, ...):
    ...

# Context manager - time specific block
async def execute(self, request):
    exec_id = request.execution_id
    async with atime_phase(exec_id, node.id, "llm_call", model="gpt-4"):
        result = await llm.complete(...)
```

### Architecture

**Core Design**:
- `TimingCollector` singleton stores timing data in memory (keyed by exec_id)
- Context managers (`time_phase`, `atime_phase`) handle timing + optional logging
- MetricsObserver retrieves data directly from collector (no file I/O)
- Optional structured logs for human inspection (not used for metrics)

**Benefits**:
- ✅ **Zero parsing overhead**: Direct in-memory access, no regex, no file scanning
- ✅ **Exception-safe**: Timings recorded even when phases throw
- ✅ **Concurrency-safe**: Keyed by exec_id, no interleaving issues
- ✅ **Production-ready**: QueueHandler for non-blocking I/O
- ✅ **Independent control**: `--timing` flag separate from `--debug`
- ✅ **Future-proof**: Easy migration path to OpenTelemetry

### Key Changes from Original Plan

Based on feedback, the architecture was revised to avoid log parsing pitfalls:

**What stayed the same**:
- Custom TIMING log level (15) for optional human-readable logs
- Phase breakdown (input → prompt → memory → LLM → output)
- CLI `--timing` flag
- Same UX for metrics display

**What changed**:
1. **No log parsing** → In-process `TimingCollector` for zero-overhead metric collection
2. **Manual timing** → Decorators (`@timed`, `@atimed`) + Context managers for exception safety
3. **f-strings everywhere** → Parameterized logging with guard checks
4. **`perf_counter`** → `perf_counter_ns` for integer math (no float drift)
5. **Inconsistent fields** → Standardized schema: `exec_id`, `node_id`, `phase`, `dur_ms`
6. **Synchronous file I/O** → `QueueHandler` for non-blocking writes
7. **Regex brittleness** → Direct dict access from collector

**Result**: Same developer experience, production-ready implementation with cleaner decorator syntax.

### ✅ Completed Phases

**Phase 1: Core Infrastructure** ✅
- `dipeo/infrastructure/timing/collector.py` - TimingCollector singleton
- `dipeo/infrastructure/timing/context.py` - Decorators & Context managers
- `dipeo/infrastructure/timing/__init__.py` - Package exports
- `dipeo/infrastructure/logging_config.py` - QueueHandler for non-blocking I/O

**Phase 2: CLI Enhancement** ✅
- Added `--timing` flag to run command
- Updated CLI runner to handle timing flag and configure logging

**Phase 3: Instrument Key Phases** ✅
- `dipeo/application/execution/handlers/person_job/single_executor.py` - Context managers for input/prompt/llm/output
- `dipeo/domain/conversation/person.py` - Context manager for complete_with_memory
- `dipeo/domain/conversation/memory_strategies.py` - Context managers for filtering/deduplication/scoring/llm_selection
- `dipeo/infrastructure/llm/drivers/service.py` - Context manager for API calls with metadata

### Phase 4: Integrate with Metrics System

#### 4.1 Update Data Model
**File**: `dipeo/application/execution/observers/metrics_types.py`

```python
@dataclass
class NodeMetrics:
    node_id: str
    node_type: str
    start_time: float
    end_time: float | None = None
    duration_ms: float | None = None
    memory_usage: int | None = None
    token_usage: dict[str, int] | None = None
    error: str | None = None
    dependencies: set[str] = field(default_factory=set)
    module_timings: dict[str, float] = field(default_factory=dict)  # NEW
```

#### 4.2 Integrate with MetricsObserver
**File**: `dipeo/application/execution/observers/metrics_observer.py`

```python
from dipeo.infrastructure.timing.collector import timing_collector

async def _handle_execution_completed(self, event: ExecutionEvent) -> None:
    execution_id = event.execution_id
    metrics = self._build_execution_metrics(execution_id)

    # Retrieve timing data directly from collector (no file I/O!)
    timing_data = timing_collector.pop(execution_id)  # pop cleans up memory

    # Merge module timings into node metrics
    for node_id, phase_timings in timing_data.items():
        if node_id in metrics.node_metrics:
            # Filter out metadata entries (end with "_metadata")
            timings = {
                phase: dur_ms
                for phase, dur_ms in phase_timings.items()
                if not phase.endswith("_metadata")
            }
            metrics.node_metrics[node_id].module_timings = timings

    # Store metrics as before
    await self._store_metrics(execution_id, metrics)
```

**Key advantages**:
- Zero file I/O overhead
- No regex parsing brittleness
- No concurrency issues
- Automatically cleaned up after retrieval (`pop`)

### Phase 5: CLI Metrics Display

#### 5.1 Add --latest Flag
**File**: `apps/server/src/dipeo_server/cli/entry_point.py`

```python
metrics_parser = subparsers.add_parser("metrics", help="Display execution metrics")
metrics_parser.add_argument("execution_id", nargs="?", help="Execution ID")
metrics_parser.add_argument("--latest", action="store_true", help="Show latest execution")
metrics_parser.add_argument("--breakdown", action="store_true", help="Show detailed phase breakdown")
```

#### 5.2 Enhanced Display
**File**: `apps/server/src/dipeo_server/cli/display.py`

```python
@staticmethod
async def display_metrics(metrics: dict[str, Any], show_breakdown: bool = False) -> None:
    print("\n📊 Execution Metrics")
    print(f"  Execution ID: {metrics.get('execution_id')}")
    print(f"  Total Duration: {metrics.get('total_duration_ms', 0):.2f}ms")

    # Module-level breakdown (only if requested or if timing was enabled)
    node_breakdown = metrics.get('node_breakdown', [])
    if node_breakdown and (show_breakdown or any(n.get('module_timings') for n in node_breakdown)):
        print("\n⏱️  Node Timing Breakdown:")
        for node_data in node_breakdown:
            node_id = node_data['node_id']
            total_ms = node_data.get('duration_ms', 0)
            module_timings = node_data.get('module_timings', {})

            if not module_timings:
                continue

            print(f"\n  {node_id} - Total: {total_ms:.0f}ms")

            # Sort by duration descending
            sorted_phases = sorted(module_timings.items(), key=lambda x: x[1], reverse=True)

            for phase, duration in sorted_phases:
                if phase == 'total':
                    continue  # Skip total (already shown)
                pct = (duration / total_ms * 100) if total_ms > 0 else 0
                print(f"    ├─ {phase:25s} {duration:7.0f}ms ({pct:5.1f}%)")
```

### Testing Plan

1. **Run with timing logs enabled**:
   ```bash
   dipeo run examples/simple_diagrams/simple_iter --light --timing --timeout=30
   ```

2. **Check timing logs (optional - for debugging only)**:
   ```bash
   grep 'dipeo.timing' .logs/cli.log | tail -20
   ```

3. **View metrics with breakdown**:
   ```bash
   dipeo metrics --latest --breakdown
   ```

4. **Run without timing (collector still works, just no logs)**:
   ```bash
   dipeo run examples/simple_diagrams/simple_iter --light --timeout=30
   dipeo metrics --latest  # Still shows module timings!
   ```

5. **Combine debug + timing**:
   ```bash
   dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=30
   ```

### Expected Output

```
📊 Execution Metrics
  Execution ID: exec_abc123
  Total Duration: 6000.00ms

⏱️  Node Timing Breakdown:

  node_1 - Total: 6000ms
    ├─ llm_completion             3500ms (58.3%)
    ├─ memory_selection           2000ms (33.3%)
    ├─ output_building             350ms ( 5.8%)
    ├─ prompt_building             100ms ( 1.7%)
    └─ input_extraction             50ms ( 0.8%)

  memory_strategy - Total: 2000ms
    ├─ llm_selection              1500ms (75.0%)
    ├─ scoring                     300ms (15.0%)
    ├─ filtering                   150ms ( 7.5%)
    └─ deduplication                50ms ( 2.5%)
```

### Remaining Files to Modify

**Phase 4 & 5**:
1. `dipeo/application/execution/observers/metrics_types.py` - Add module_timings field
2. `dipeo/application/execution/observers/metrics_observer.py` - Retrieve from collector
3. `apps/server/src/dipeo_server/cli/entry_point.py` - Add --breakdown flag to metrics command
4. `apps/server/src/dipeo_server/cli/display.py` - Display module breakdown

### Migration Path to OpenTelemetry (Future)

When ready for distributed tracing, the migration is straightforward:

```python
# Replace time_phase with OpenTelemetry span
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

# Before:
with time_phase(exec_id, node_id, "input_extraction"):
    result = extract_inputs(data)

# After:
with tracer.start_as_current_span("input_extraction", attributes={"exec_id": exec_id, "node_id": node_id}):
    result = extract_inputs(data)
```

Same context manager pattern, just swap the implementation.

### Priority
**High** - Developer productivity improvement with production-ready architecture
