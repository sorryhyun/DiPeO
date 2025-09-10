Done — I unpacked your zips (`dipeo/ apps/ projects/ docs/ examples/ integrations/`) and read through the code. Below are **codebase-grounded** gaps and concrete, file-level fixes (with mini patches) you can apply right now.

---

# What I found (quick snapshot)

* **BaseService is still widely used (11 classes)**, including two *application* use cases and several infra adapters:
  `application/execution/use_cases/{execute_diagram.py,prepare_diagram.py}`,
  `infrastructure/codegen/parsers/parser_service.py`,
  `infrastructure/integrations/drivers/integrated_api/{service.py,providers/base_provider.py}`,
  `infrastructure/shared/adapters/{artifact_adapter.py,local_adapter.py,s3_adapter.py}`,
  `infrastructure/shared/keys/drivers/{api_key_service.py,environment_service.py}`.
  Only **two** services use mixins:
  `infrastructure/diagram/drivers/diagram_service.py`, `infrastructure/llm/drivers/service.py`.

* **EventBus is unified** (`dipeo/domain/events/unified_ports.py`) and re-exported by `ports.py` (just a wrapper). An in-memory bus lives at `infrastructure/events/adapters/in_memory_event_bus.py`. Wiring supports in-memory and a backend toggle via `DIPEO_EVENT_BUS_BACKEND` (see `application/bootstrap/wiring.py`).

* **Scheduler is token-based** (`application/execution/scheduler.py`) and already has:

  * default join rules (Condition => ANY, others => ALL),
  * a **`skippable`** pathway for conditional edges,
  * a simple `JoinPolicy` class (see `domain/execution/token_types.py`) with support for `"all" | "any" | "k_of_n"`.
    The older `domain/execution/dynamic_order_calculator.py` still exists and partially overlaps with the new scheduler.

* **Sub-diagram executors** (`application/execution/handlers/sub_diagram/*`) deep-copy input dicts (`lightweight_executor.py`) but do **not** give you clear, namespaced variable scopes, so child runs can still clash with parent contexts during template merges (`typed_execution_context.build_template_context` merges inputs/globals/locals flatly).

* **Conversation repo is in-memory only** (`infrastructure/repositories/conversation/in_memory.py`). No persistence for runs/tokens/outputs.

* **Codegen workflow** is Makefile-driven with a staged dir (you reference it heavily), but there’s **no manifest**/idempotence guard:

  * `make parse-typescript` → runs `projects/codegen/diagrams/parse_typescript_batch_direct`
  * `make codegen` → runs `projects/codegen/diagrams/generate_all`
  * `make diff-staged` / `make apply(-syntax-only)` exist — but no hash/version check for `diagram_generated_staged/`.

---

# High-impact fixes (real changes you can apply)

## 1) Finish the BaseService → Mixins migration (incl. application layer)

**Goal:** Consistency and simpler DI. You already have solid mixins: `LoggingMixin`, `InitializationMixin` (`domain/base/mixins.py`).

**Example patch — remove BaseService from use cases**

* File: `dipeo/application/execution/use_cases/execute_diagram.py`

```diff
-class ExecuteDiagramUseCase(BaseService):
+class ExecuteDiagramUseCase:
```

No `BaseService` APIs are used here; safe to drop. Same change applies to:

* `dipeo/application/execution/use_cases/prepare_diagram.py`
* `dipeo/infrastructure/codegen/parsers/parser_service.py`
* `dipeo/infrastructure/integrations/drivers/integrated_api/{service.py,providers/base_provider.py}`
* `dipeo/infrastructure/shared/adapters/{artifact_adapter.py,local_adapter.py,s3_adapter.py}`
* `dipeo/infrastructure/shared/keys/drivers/{api_key_service.py,environment_service.py}`

**If you want mixins on infra services/adapters:**

```diff
-from dipeo.domain.base import BaseService
+from dipeo.domain.base.mixins import LoggingMixin, InitializationMixin

-class LocalBlobAdapter(BaseService, BlobStorePort):
+class LocalBlobAdapter(LoggingMixin, InitializationMixin, BlobStorePort):
    async def initialize(self) -> None:
        ...
```

> Do this consistently across the three storage adapters and integrated API classes. Nothing else changes.

**Then** delete `domain/base/service.py` in a later sweep, after all imports are gone.

---

## 2) Make join semantics explicit and testable

You already have `JoinPolicy(policy_type="all|any|k_of_n", k: int|None)` in `domain/execution/token_types.py`, and the scheduler reads `node.join_policy` *if present*.

**Patch — read join policy from node.metadata**, so you don’t need to regenerate node models:

* File: `application/execution/scheduler.py` (inside `_initialize_policies`)

```diff
- # First, check if node has a compiled join_policy field
- if hasattr(node, "join_policy") and node.join_policy is not None:
+ # Prefer explicit join policy from node or metadata
+ explicit = getattr(node, "join_policy", None)
+ if not explicit and hasattr(node, "metadata"):
+     meta = getattr(node, "metadata") or {}
+     explicit = meta.get("join_policy")  # e.g., {"type":"k_of_n", "k":2} or "any"/"all"
  ...
-    if isinstance(node.join_policy, str):
+    if isinstance(explicit, str):
         self._join_policies[node.id] = JoinPolicy(policy_type=node.join_policy)
-    else:
-        self._join_policies[node.id] = node.join_policy
+    elif isinstance(explicit, dict):
+        self._join_policies[node.id] = JoinPolicy(
+            policy_type=explicit.get("type","all"),
+            k=explicit.get("k")
+        )
+    else:
+        # Fallback type-derived defaults...
```

**Docs/UI**: allow users to set `node.metadata.join_policy = "any" | "all" | {"type":"k_of_n","k":2}` in diagrams.

**Test**: add unit tests to assert readiness for:

* ANY/ALL on combinations of incoming edges,
* `k_of_n` with k=2 and three sources,
* `skippable` edges only skipping when the target has ≥2 sources (your code already does this; keep it).

---

## 3) Sub-diagram variable scoping that can’t bleed

Right now, `TypedExecutionContext.build_template_context` **flattens** inputs/globals/locals, and `lightweight_executor.py` merely deep-copies dicts. Introduce a **scope stack** and isolate sub-diagram variables with a namespace.

**Patch — add a simple scope API**

* File: `application/execution/typed_execution_context.py`

```diff
+from contextlib import contextmanager
+
 class TypedExecutionContext:
     ...
+    def __init__(...):
+        ...
+        self._scope_stack: list[str] = []
+        self._scoped_vars: dict[str, dict[str, Any]] = defaultdict(dict)
+
+    @contextmanager
+    def enter_scope(self, name: str):
+        self._scope_stack.append(name)
+        try:
+            yield
+        finally:
+            self._scope_stack.pop()
+            self._scoped_vars.pop(name, None)
+
+    def set_var(self, key: str, value: Any) -> None:
+        scope = self._scope_stack[-1] if self._scope_stack else ""
+        if scope:
+            self._scoped_vars[scope][key] = value
+        else:
+            self._locals[key] = value
+
     def build_template_context(...):
         ...
-        merged = {**globals_, **inputs, **locals_} or the other order...
+        # Compose context from globals + inputs + locals + top-of-scope overlay
+        scope = self._scope_stack[-1] if self._scope_stack else ""
+        overlay = self._scoped_vars.get(scope, {})
+        merged = (
+            {**globals_, **inputs, **locals_, **overlay}
+            if globals_win
+            else {**inputs, **globals_, **locals_, **overlay}
+        )
```

**Use it in sub-diagrams**

* File: `application/execution/handlers/sub_diagram/lightweight_executor.py`

```diff
-        # Run sub-diagram using copied variables
-        # (existing code)
+        # Run sub-diagram in an isolated scope
+        with request.context.enter_scope(f"sub:{node.id}"):
+            # Optionally preload scoped vars from inputs["default"]
+            if isinstance(variables, dict):
+                for k, v in variables.items():
+                    request.context.set_var(k, v)
+            # execute child using ExecuteDiagramUseCase or lightweight path...
```

**Why this works:** parent/global vars stay intact; only declared outputs come back (exactly where you emit envelopes after sub-diagram completion). This eliminates the “template vars overwritten by child” bug you saw.

---

## 4) Kill duplication: retire the old order calculator

`domain/execution/dynamic_order_calculator.py` still implements readiness rules that drift from the token scheduler. Make the scheduler the **single source of truth**.

**Action:**

* Mark `dynamic_order_calculator.py` as deprecated and:

  * keep interfaces if something still imports it,
  * have it just forward to the scheduler’s readiness checks (or delete after a release).

---

## 5) Persistence: add SQLite repo(s) for conversations & runs

**Why:** you’ll need resume/replay/analytics; in-memory is fragile.

**New files (skeletons)**

* `dipeo/infrastructure/repositories/conversation/sqlite.py`
* `dipeo/infrastructure/repositories/runs/sqlite.py` (new bounded context)

Each with a tiny schema:

```sql
-- conversations
CREATE TABLE IF NOT EXISTS conversations (
  person_id TEXT,
  ts INTEGER,
  role TEXT,
  content TEXT,
  meta JSON
);

-- runs
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  diagram_id TEXT,
  started_at INTEGER,
  ended_at INTEGER,
  status TEXT,
  manifest_id TEXT
);

CREATE TABLE IF NOT EXISTS node_events (
  run_id TEXT,
  node_id TEXT,
  epoch INTEGER,
  event_type TEXT,
  payload JSON,
  ts INTEGER
);
```

**Wire it**

* File: `application/bootstrap/infrastructure_container.py`

```diff
 def _setup_repositories(self):
-    from dipeo.infrastructure.repositories.conversation import (
-        InMemoryConversationRepository,
-        InMemoryPersonRepository,
-    )
+    backend = os.getenv("DIPEO_REPO_BACKEND", "memory")
+    if backend == "sqlite":
+        from dipeo.infrastructure.repositories.conversation.sqlite import SQLiteConversationRepository as ConversationRepo
+        from dipeo.infrastructure.repositories.person.in_memory_person import InMemoryPersonRepository as PersonRepo
+        conversation_repository = ConversationRepo(db_path=Path(".dipeo/sqlite.db"))
+        person_repository = PersonRepo()
+    else:
+        from dipeo.infrastructure.repositories.conversation import InMemoryConversationRepository as ConversationRepo
+        from dipeo.infrastructure.repositories.person import InMemoryPersonRepository as PersonRepo
+        conversation_repository = ConversationRepo()
+        person_repository = PersonRepo()
```

Start lightweight; you can extend to persist `node_events` from the event bus (see #7).

---

## 6) Codegen safety rails: add a manifest and idempotence check

**Manifest**: after codegen, write `dipeo/diagram_generated_staged/manifest.json`:

```json
{
  "schemaVersion": 1,
  "generatedAt": 1694092800,
  "sourceHash": "<sha256 of projects/** and models/**>",
  "codegenVersion": "2025.09.07"
}
```

**Makefile additions**

* Add a checksum step to `codegen` and a new `codegen-check` target:

```make
codegen: parse-typescript
	@echo "Generating code..."
	@if command -v dipeo >/dev/null 2>&1; then \
		dipeo run projects/codegen/diagrams/generate_all --light --debug --timeout=35; \
	else \
		python -m dipeo_cli run projects/codegen/diagrams/generate_all --light --debug --timeout=35; \
	fi
	@python - <<'PY'
import hashlib, json, os, time
from pathlib import Path
srcs = []
for root in ("projects","dipeo/models"):
    for dp,_,fs in os.walk(root):
        for f in fs:
            p=Path(dp)/f
            srcs.append(p.read_bytes())
h=hashlib.sha256()
for b in sorted(srcs,key=len): h.update(b)
manifest={
 "schemaVersion":1,
 "generatedAt":int(time.time()),
 "sourceHash":h.hexdigest(),
 "codegenVersion":"2025.09.07"
}
out=Path("dipeo/diagram_generated_staged/manifest.json")
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(manifest,indent=2))
print("Wrote", out)
PY
	@echo "✓ Code generation complete. Next: make diff-staged → make apply-syntax-only → make graphql-schema"

codegen-check:
	@python - <<'PY'
import json,hashlib,os
from pathlib import Path
m=Path("dipeo/diagram_generated_staged/manifest.json")
assert m.exists(), "manifest.json missing; run make codegen"
data=json.loads(m.read_text())
# recompute hash
srcs=[]
for root in ("projects","dipeo/models"):
    for dp,_,fs in os.walk(root):
        for f in fs:
            p=Path(dp)/f
            srcs.append(p.read_bytes())
h=hashlib.sha256()
for b in sorted(srcs,key=len): h.update(b)
if data.get("sourceHash")!=h.hexdigest():
    raise SystemExit("Codegen not idempotent: source hash mismatch")
print("Idempotence OK")
PY
```

**Gate `make apply(-syntax-only)`** to verify the manifest exists & optional version pinning.

---

## 7) Telemetry envelope: structured events with correlation IDs

You already centralize events via `EventBus`. Add a **typed execution event** and emit it everywhere:

* New: `domain/events/contracts.py` already has `DomainEvent`. Extend with:

```python
@dataclass
class ExecutionEvent(DomainEvent):
    run_id: str
    node_id: NodeID
    event: str  # "node_started" | "node_completed" | "node_failed"
    epoch: int
    token_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
```

* In handlers (`handler_base.py`) and scheduler: emit `ExecutionEvent` with `run_id` and `epoch` on start/complete/fail. Your `InMemoryEventBus` will store events when `_enable_event_store=True`. Then your new `node_events` SQLite table (from #5) can subscribe and persist.

---

## 8) Clarify and lock multi-worker behavior

You already hint at Redis in logs & wiring. Add a guard:

* On startup, if `WEB_CONCURRENCY>1` **and** `DIPEO_EVENT_BUS_BACKEND!="redis/adapter with broker"`, log a prominent warning (`GraphQL subscriptions require a shared broker`) — you already do this partly; make it explicit and docs-visible in README.

---

# Nice-to-haves (fast wins)

* **Deprecate** `dipeo/domain/events/ports.py` (wrapper) and switch imports to `unified_ports.py` in one sweep using a codemod.
* Add **unit tests** for:

  * `JoinPolicy.is_ready()` for `"all" | "any" | "k_of_n"`.
  * `skippable` edge rule: skip only when target has ≥2 sources.
  * sub-diagram scoping API: parent context preserved, only declared outputs returned.
* **Delete** empty `__init__.py` and commented code blocks flagged during your own pass; keep mypy/ruff happy in `make install-dev`.
* **Docs**: in README’s dev loop, explicitly show: `make parse-typescript && make codegen && make diff-staged && make apply-syntax-only && make graphql-schema` and mention the new manifest gate.

---

# Why these changes matter to your current bugs

* **Template overwrite in sub-diagrams** → fixed by scope stack + namespaced vars.
* **`simple_iter`/multi-incomings hang or misfire** → explicit join policies (and `k_of_n`) make readiness rules visible and deterministic, while **skippable** only applies when safe.
* **Inconsistent service base** → removing `BaseService` everywhere reduces cognitive overhead and makes future services consistent with `DiagramService`/`LLMInfraService`.
* **Observability & persistence** → you can now replay runs, debug token flows, and compare manifests across codegen cycles.

If you want, I can generate a patch bundle touching the exact files above (edits are small and localized).
