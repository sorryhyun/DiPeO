# RFC: Strict Envelopes & Arrow Contracts (SEAC)

**Status**: Partially Implemented (August 2025) - Core functionality complete, port contracts pending

**Goal** Make codegen diagrams flexible for users (tweak how data passes through an arrow) while **eliminating implicit fallbacks** like `results`, `default`, or `is_dict()` checks. Ensure direct list/dict delivery with zero/minimal copying.

---

## TL;DR / What changes for authors

- Keep using `and` on connections. That’s the contract.
- If you send a **dict** or **list** via `content_type: object`, the target node **receives it as-is**, mapped by the connection **label** (no wrapping under `results`, no auto-shape guessing).
- Unlabeled inputs are only allowed **when a node declares a single unnamed port**; otherwise the compiler errors out.
- Batch `sub_diagram` can emit **pure lists** (new default) or a **rich object** (opt-in) via `output_mode`.

---

## Problems today

1. **Implicit wrappers & fallbacks**
   - Code paths that auto-wrap lists at the `default` key into `{ "results": [...] }`.
   - Handlers probing with `is_dict()` or searching for magic keys like `results` or `default`.
2. **Ambiguous merges**
   - Multiple incoming edges without labels leads to heuristic merges and surprises.
3. **Serialization churn**
   - JSON stringify/parse or envelope-to-text-to-JSON detours even when both ends already speak Python objects.

---

## The proposal

### 1) **Strict Envelopes** (runtime)

- **Envelope.body is authoritative.** No shape mutation based on heuristics.
- **Type-driven extraction only**:
  - `raw_text` → `str`
  - `object` → `dict | list | pydantic model`
  - `conversation_state` → structured conversation payload
- No `is_dict()` path splitting and **no auto-wrapping** (e.g., removing the default-key special case).
- Large payloads (e.g., NumPy) use \`\` hints; within-process, pass references **zero-copy**. (Inter-process fallback: `.npy`/`.npz` via object store when we add it.)

### 2) **Arrow Contracts** (compile-time)

- **Connection.label** decides the variable name in the target node.
- **Connection.content\_type** states how to interpret the payload.
- New optional \`\` (default `pack`):
  - `pack` → bind to the variable named by `label`. (Current behavior.)
  - `spread` → shallow-merge dict keys into the node’s input namespace (error on collisions). If value isn’t a dict, this is a compile-time error. *Rationale*: lets authors keep just label/content-type for most flows; `spread` is a minimal addition for power users who want to “pour” objects into kwargs without an extra wrapper.

### 3) **Port Contracts** (node specs → codegen)

- Each node type declares **input ports** with:
  - `name` (or unnamed single port), `content_type` (one of: `raw_text | object | conversation_state | binary`), `required: bool`, optional `accepts: list[type-hints]`.
- Codegen produces a **typed input model** (`Pydantic`) for each node handler and the UI schema.
- **Compiler validates**:
  - Labeled edges land on existing port names (or unnamed single port).
  - Content types are compatible (with exact or declared coercions).
  - `spread` only into ports that allow it and with non-colliding keys.

### 4) **Sub-diagram batch: direct list delivery**

- Add `props.output_mode` to `sub_diagram`:
  - `pure_list` (default new) → envelope body is `list[ItemResult]` (no `{results: …}` wrapper). Batch metadata goes to \`\` (`total_items`, `failed`, etc.).
  - `rich_object` (compat) → `{results: [...], errors: [...], ...}` body as today.
- Add `props.result_key` (optional) to name the list key in `rich_object` mode (default `results`).

### 5) **One unnamed input rule**

- If a node declares exactly **one unnamed input port**, unlabeled edges can target it. Otherwise, **labels are mandatory**.
- This replaces ad-hoc use of a magic `default` variable.

---

## Implementation Status

### ✅ Completed (August 2025)

1. **Feature Flag**: `STRICT_ENVELOPES` environment variable controls strict behavior
2. **CodeJob Handler**: Direct list/dict passing without auto-wrapping when enabled
3. **SubDiagram Batch**: 
   - Added `output_mode` property (`pure_list` | `rich_object`)
   - Added `result_key` property for customizing wrapper key
4. **Updated Models**: Properties added to all generated models
5. **Diagram Compatibility**: Codegen diagrams updated to handle both structures

### 📋 Remaining Tasks

**C. Input resolution pipeline – enforce contracts**

- In `IncomingEdgesStage`: keep `Envelope` → **value** extraction based on `content_type` only; no structural edits.
- In `TransformStage`: add `packing` rule (`pack|spread`).
- In `DefaultsStage`: only apply **declared port defaults**; remove type-based or global fallbacks.

**D. Node spec (models) – declare ports**

```ts
// models/src/node-specs/code_job.spec.ts
inputs: [
  { name: "default", contentType: "object", required: false },
  { name: "code", contentType: "raw_text", required: true },
]
```

Codegen emits a Pydantic model for handler `execute(input: CodeJobInput)`.

---

## Light YAML examples

**Direct dict/list pass-through**

```yaml
connections:
  - from: Load JSON
    to: Transform
    content_type: object
    label: data    # Transform receives `data` exactly as produced
```

**Spread merge (advanced)**

```yaml
connections:
  - from: Parse Config
    to: Run
    content_type: object
    label: cfg
    packing: spread  # shallow-merge cfg.{*} into Run’s inputs (compile-time collision check)
```

**Batch sub-diagram → pure list**

```yaml
- label: Process Items
  type: sub_diagram
  props:
    diagram_name: workflows/process_single
    batch: true
    batch_input_key: items
    batch_parallel: true
    output_mode: pure_list  # envelope.body is just the array
```

---

## Migration & compatibility

- **Feature flag**: `STRICT_ENVELOPES=1` (backend env) to enable new behavior. Currently defaults to `0` for backward compatibility.
- **Future default**: Plan to make `STRICT_ENVELOPES=1` the default behavior in Q1 2026, with legacy mode requiring explicit `STRICT_ENVELOPES=0`.
- **Codegen compatibility**: Diagrams updated to handle both wrapped and direct structures automatically.
- **Deprecation path**: 
  - Current: `STRICT_ENVELOPES=0` (default) - legacy behavior
  - Q4 2025: Emit warnings for implicit wrapping behaviors
  - Q1 2026: `STRICT_ENVELOPES=1` becomes default
  - Q2 2026: Remove legacy behavior entirely

---

## Test plan

1. Unit tests for `CodeJob`, `DB`, `sub_diagram` to confirm **no shape mutation**.
2. Pipeline tests for `packing: spread` collision errors and unlabeled-edge validation.
3. Perf tests with large lists/dicts and NumPy arrays to ensure **zero-copy** paths.
4. Back-compat tests: run existing codegen diagrams under `rich_object` and ensure no regressions.

---

## Expected impact

- **Predictability**: inputs and outputs match exactly what arrows carry.
- **Simplicity**: remove magic keys/fallbacks; fewer branches in handlers.
- **Performance**: less serialization and fewer copies; better batch/parallel throughput.
- **User control**: authors choose mapping via labels (and optional `packing`), not by implied conventions.

---

## Next steps

- Add `packing` to connection schema (UI + compiler + runtime TransformStage) for `spread` merge support.
- Implement port contracts in node specifications with explicit input/output declarations.
- Update documentation with examples showing migration from legacy to strict mode.
- Add telemetry to track usage patterns and identify diagrams that would benefit from strict mode.
- Create migration tool to automatically update existing diagrams for `STRICT_ENVELOPES=1` compatibility.

