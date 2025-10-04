Short take: your plan will work and is a nice “zero new infra” way to get phase timings fast. The two big pitfalls are (1) log-parsing brittleness under concurrency and (2) hidden overhead from string formatting and file I/O on hot paths. I’d keep the *spirit* (reuse logger) but change the *mechanics* so you don’t have to scrape your own logs.

Here’s a concrete, leveled take:

## What’s solid

* You’ve identified the right phases (input → prompt → memory → LLM → output → total). That’s the breakdown you’ll actually optimize.
* `perf_counter` and measuring around awaitable boundaries give true wall time, which is what you want for “user-perceived” latency.
* Surfacing a CLI `--latest` with a per-node breakdown is exactly what devs will reach for during a perf triage.

## Key issues to fix (high ROI)

1. **String formatting overhead (hot path)**

   * All your examples use f-strings. Those render even when DEBUG is off.
   * Fix: use parameterized logging or a guard:

     ```python
     if logger.isEnabledFor(logging.DEBUG):
         logger.debug("[TIMING] node=%s phase=%s duration_ms=%.2f execution_id=%s",
                      node.id, "prompt_building", duration, trace_id)
     ```
   * Or better, use `extra={}` and let the formatter/handler render.

2. **Inconsistent fields → broken attribution**

   * You sometimes log `node=...` and elsewhere `person=...`. Your parser only knows `node=...`.
   * Fix: standardize **one schema**: `exec_id`, `diagram_id`, `node_id`, `phase`, `dur_ms`, `ts`.
   * Make sure **every** timing log line includes `exec_id` and `node_id` (even deep inside memory strategies).

3. **Regex will break on real IDs**

   * `\w+` won’t match UUIDs with hyphens. Use a more forgiving token class:

     ```python
     r'node_id=(?P<node>[^ \t]+)'
     ```
   * Ditto for `exec_id`. Also: filter by parsed `exec_id`, not `if execution_id in line`.

4. **Losing timings on exceptions**

   * Your samples log after successful awaits. If a phase throws, you lose the measurement.
   * Fix: a tiny context manager (and async variant) that logs in `finally`.

5. **Log parsing scalability & rotation**

   * Reading `.logs/cli.log` every time and scanning is O(file_size) and race-y with rotation.
   * Fix: either keep an offset checkpoint or—better—avoid parsing entirely (see “Better design” below).

6. **Concurrency & interleaving**

   * Multiple executions interleave lines; order isn’t guaranteed. Require `exec_id` and `node_id` on **every** line and don’t rely on adjacency.

7. **I/O on hot path**

   * If you crank up logging during load, synchronous file writes will bite you.
   * Fix: use `QueueHandler` + `QueueListener` so the producer thread is non-blocking.

## Minimal code tweaks (drop-in)

**A. Central timing helper (works for sync/async, logs even on exceptions):**

```python
import time, logging
from contextlib import contextmanager, asynccontextmanager

log = logging.getLogger("dipeo.timing")

@contextmanager
def time_phase(exec_id: str, node_id: str, phase: str, **fields):
    if not log.isEnabledFor(logging.DEBUG):
        yield
        return
    start = time.perf_counter_ns()
    try:
        yield
    finally:
        dur_ms = (time.perf_counter_ns() - start) / 1_000_000
        log.debug(
            "[TIMING] exec_id=%s node_id=%s phase=%s dur_ms=%.3f",
            exec_id, node_id, phase, dur_ms, extra={"timing": {**fields}}
        )

@asynccontextmanager
async def atime_phase(exec_id: str, node_id: str, phase: str, **fields):
    with time_phase(exec_id, node_id, phase, **fields):
        yield
```

Usage:

```python
async def execute(...):
    with time_phase(trace_id, node.id, "input_extraction"):
        extracted_inputs = self._extract_inputs(inputs)

    async with atime_phase(trace_id, node.id, "complete_with_memory"):
        result, incoming_msg, response_msg, selected = await person.complete_with_memory(...)
```

**B. Always structured; stop scraping free-text**
Use a JSON formatter (e.g., `python-json-logger` or `structlog`) so the record has first-class fields:

```json
{"ts":"...","level":"DEBUG","event":"TIMING","exec_id":"...","node_id":"...","phase":"prompt_building","dur_ms":12.34}
```

Then your “parser” is just a line-by-line JSON read + field filter—no brittle regex.

**C. Dedicated logger & level**
Create a separate logger (`dipeo.timing`) with its own level and handler. You can run:

* app debug logs off
* timing logs on (INFO or DEBUG)
  …and vice-versa. That’s better than “use a lower debug level” globally.

```python
TIMING_LEVEL = 9  # custom TRACE-like
logging.addLevelName(TIMING_LEVEL, "TIMING")
def timing(self, msg, *args, **kw): self.log(TIMING_LEVEL, msg, *args, **kw)
logging.Logger.timing = timing
```

Now you can enable/disable timing independently without polluting regular DEBUG.

## Better design (same UX, no log scraping)

**Option 1 — In-process collector (my pick for you right now)**

* Introduce a tiny singleton `TimingCollector` keyed by `exec_id`.
* The context manager above calls `TimingCollector.record(exec_id, node_id, phase, dur_ms)` **and** logs (for humans).
* `MetricsObserver` reads directly from the collector on completion—zero file I/O, no regex, race-free.

Sketch:

```python
from collections import defaultdict

class TimingCollector:
    def __init__(self):
        self._data = defaultdict(lambda: defaultdict(dict))
    def record(self, exec_id, node_id, phase, dur_ms):
        self._data[exec_id][node_id][phase] = self._data[exec_id][node_id].get(phase, 0) + dur_ms
    def pop(self, exec_id):
        return self._data.pop(exec_id, {})

timings = TimingCollector()

# in time_phase.__exit__
timings.record(exec_id, node_id, phase, dur_ms)
```

* Keep logs for humans; trust the collector for the CLI.
* Overhead: a dict write and (optional) a queued log—tiny.

**Option 2 — OpenTelemetry tracing (future-proof)**

* Map each phase to a span (`exec_id` → trace; `node_id` → span name attribute).
* You get nested spans “for free” (memory_selection → scoring → llm_selection).
* Exporters: console (dev), OTLP to Jaeger/Tempo/Lightstep (prod).
* Your CLI can query the in-proc span data if you use the in-memory exporter, or you can read back from the backend.
* Heavier to wire initially but pays off for distributed nodes and multi-process.

**Option 3 — Prometheus histograms (fleet health)**

* Not great for per-execution breakdowns, but invaluable for SLOs: `dipeo_phase_duration_ms{phase,node_type}`.
* Use alongside Option 1 or 2.

## Phase taxonomy & counters (small upgrades)

* Split LLM time into: `llm_queue`, `llm_api`, `llm_stream_ttft`, `llm_stream_tokens` (if streaming). Compute tokens/sec and TTFT; those drive perceived latency.
* Capture token counts (you already have them) to report cost and throughput: `tokens_total / llm_api_ms`.
* For memory strategy, keep hierarchical phases; your CLI already prints a tree—good.

## Parser hardening (if you must parse logs)

* Switch to JSON lines; stop using regex.
* If you must keep regex, fix patterns: accept hyphens; don’t substring-filter; parse then compare; handle rotations with a simple offset index.
* Add unit tests with interleaved execs and partial lines.

## Operational hygiene

* Make timing logs opt-in (`--timing`), independent from `--debug`.
* Use `QueueHandler` to avoid file I/O on the request thread.
* Consider per-execution temp files **only** if you insist on parsing; name by `exec_id` to avoid O(file_size).

## Answering your “lower debugging level” idea

Using a lower level (e.g., INFO) will “work”, but it’ll either spam normal logs or force you to downshift all DEBUG. A cleaner separation is:

* Keep normal app logs at INFO/DEBUG on `dipeo.*`.
* Put timing on `dipeo.timing` at `TIMING` (custom) or INFO with a dedicated handler/output. Then you can toggle timing independently without changing developer log verbosity.

## Tiny correctness nits in your draft

* Standardize fields: **always** include `exec_id` and `node_id` everywhere (memory strategy logs are missing `node_id`, and `person=` doesn’t match your parser).
* Wrap every phase in try/finally (or the context manager) so exceptions still emit durations.
* Prefer `perf_counter_ns()` (integer math, no float drift), then render ms at the edge.
* `metrics_observer.parse_timing_logs`: reading the whole file each time is risky; at minimum, cache the file offset you last consumed.

---

### Bottom line

Keep the UX and phases you designed, but stop scraping text logs for metrics. Add a tiny in-process `TimingCollector` (plus the context manager), and optionally still emit structured JSON timing logs for humans. If/when you need cross-process or distributed traces, promote the same phases to OpenTelemetry spans. This gives you accurate, low-overhead measurements now and a sane path to real tracing later.
