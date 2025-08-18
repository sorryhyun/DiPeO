# Why it feels “stopped”

**What’s already there (from the repo you attached):**

- `dipeo/application/graphql/schema_factory.py` builds the Strawberry schema and already imports generated enums & domain models, but **the **``** list is commented / not populated** — so generated node data types aren’t actually registered in the schema yet.
- `dipeo/application/graphql/schema/subscriptions.py` streams execution events and pulls `EventType` & IDs from `dipeo/diagram_generated`, but **payloads are still exposed as **``, not strong, generated GraphQL types.
- `dipeo/diagram_generated/graphql/strawberry_nodes.py` is a **single, consolidated file** defining Strawberry `@pydantic.type` wrappers for *all* node `...NodeData`. Meanwhile, `dipeo/diagram_generated/models/` and `.../nodes/` are already **nicely split per-node** — the inconsistency is what you’re seeing.
- `apps/server` mounts GraphQL using the application schema (`create_schema`), and `dipeo/application/graphql/export_schema.py` can export a schema for codegen — the plumbing is there, we just need to finish the hand‑off to the generated pieces.

---

# Goals

1. **Register all generated Strawberry types** (node data, domain add‑ons) into the app schema with zero manual upkeep.
2. **Replace ad‑hoc JSON payloads** in subscriptions and queries with **strong, generated GraphQL types**.
3. **De‑monolithize** `strawberry_nodes.py` into per‑node files (with an aggregator) so it matches your already-split `models/` and `nodes/` layout.
4. Keep **backwards compatibility** for anything currently importing from consolidated files.

---

# Step‑by‑step implementation

## 1) Auto‑register generated types in the schema

**Files:** `dipeo/application/graphql/schema_factory.py` (edit)

Add a tiny loader that imports all classes ending with `DataType` from `dipeo.diagram_generated.graphql`, whether they live in one file or many.

```python
# dipeo/application/graphql/schema_factory.py
import importlib
import inspect
from types import ModuleType

GEN_PKG = "dipeo.diagram_generated.graphql"

def _collect_generated_types() -> list[type]:
    types: list[type] = []

    # 1) Load root package
    pkg = importlib.import_module(GEN_PKG)

    # 2) Explore known modules (works for monolith or split files)
    candidates = [
        getattr(pkg, name)
        for name in dir(pkg)
        if not name.startswith("__")
    ]

    # If a subpackage "nodes" exists, include it
    try:
        nodes_pkg = importlib.import_module(f"{GEN_PKG}.nodes")
        candidates.append(nodes_pkg)
        candidates.extend(
            importlib.import_module(f"{GEN_PKG}.nodes.{m}")
            for m in getattr(nodes_pkg, "__all__", [])
        )
    except ModuleNotFoundError:
        pass

    # 3) Collect all classes ending with DataType
    def collect_from(mod: ModuleType):
        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if obj.__module__.startswith(GEN_PKG) and obj.__name__.endswith("DataType"):
                types.append(obj)

    for c in candidates:
        if isinstance(c, ModuleType):
            collect_from(c)

    return types
```

Then wire it into schema creation:

```python
# inside create_schema(...)
from dipeo.application.graphql.types.domain_types import (
    DiagramType, NodeType, ExecutionType, # etc.
)

generated_types = _collect_generated_types()

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(auto_camel_case=False),
    types=[*generated_types, DiagramType, NodeType, ExecutionType],
)
```

✅ **Result:** all generated node data GraphQL types are part of the schema automatically.

---

## 2) Strongly‑typed subscription payloads

**Files:** `dipeo/application/graphql/schema/subscriptions.py` (edit)

Right now we yield `JSONScalar`. Replace with **unions of concrete payload types**. Start small:

```python
# Define thin Pydantic models for events (or reuse generated ones)
@strawberry.type
class ExecutionLogPayload:
    execution_id: str
    level: str
    message: str
    timestamp: str

@strawberry.type
class NodeStatusChangedPayload:
    execution_id: str
    node_id: str
    status: Status  # from generated enums via Strawberry enum mapping
    timestamp: str

ExecutionEventPayload = strawberry.union(
    "ExecutionEventPayload",
    (ExecutionLogPayload, NodeStatusChangedPayload)
)

@strawberry.type
class ExecutionUpdate:
    execution_id: str
    event_type: EventType
    data: ExecutionEventPayload
    timestamp: str
```

…and map `EventType → payload` in the streaming loop. Incrementally add more cases (node completed, started, etc.). Keep a fallback to `JSONScalar` behind a feature flag until everything is typed.

---

## 3) Split `strawberry_nodes.py` into per‑node files (generator change)

**Files:** `projects/codegen/templates/models/…` (new templates) & generator code

Add a v2 template that renders **one file per node** like:

```
/dipeo/diagram_generated/graphql/nodes/
  api_job.py (ApiJobDataType)
  code_job.py (CodeJobDataType)
  ...
__init__.py  # exports __all__ for the loader
```

**Jinja sketch** (per‑node):

```jinja2
{# templates/graphql/node_datatype.j2 #}
"""Strawberry type for {{ node.name }} node data."""
import strawberry
from dipeo.diagram_generated.models.{{ node.snake }}_model import {{ node.data_class }}

@strawberry.experimental.pydantic.type({{ node.data_class }}, all_fields=True)
class {{ node.pascal }}DataType:
    """{{ node.description }} – Data fields only"""
    pass
```

**Aggregator** `__init__.py` template:

```jinja2
# auto-generated
__all__ = [
{% for n in nodes %}    "{{ n.snake }}",
{% endfor %}]

# Re-export per-node modules for simple imports
{% for n in nodes %}from . import {{ n.snake }}
{% endfor %}
```

Update the generation diagram to:

- iterate nodes → write `nodes/<snake>.py`
- write `nodes/__init__.py`
- keep writing **legacy** `strawberry_nodes.py` for now, behind `SPLIT_GRAPHQL_FILES=true` flag (env or config) to allow gradual migration.

---

## 4) Keep compatibility for consolidated imports

If other code imports from the monolith, provide a **compat shim**:

```python
# dipeo/diagram_generated/graphql/__init__.py
# import everything from new nodes package so old imports keep working
from .nodes import *  # noqa: F401,F403
```

Optionally, re‑generate a thin `strawberry_nodes.py` that only re‑exports the per‑node classes for one release cycle and mark it deprecated in the file header.

---

## 5) Let queries & mutations surface generated types

**Files:** `dipeo/application/graphql/schema/queries.py`, `mutation_factory.py`, resolvers

- For any resolver returning a node’s data, **return the Pydantic model** from `dipeo.diagram_generated.models.*` — Strawberry will project it into the matching `...DataType` automatically.
- Adjust field selections in your generated queries (`dipeo/models/src/frontend/query-definitions/**/*.ts`) where needed so the frontend actually **pulls** those structured fields (not just strings) and the codegen emits typed hooks.

> You already have the pipeline that writes `apps/web/src/__generated__/queries/all-queries.ts` from those TS definitions; use that as the single source of truth so the web codegen remains hands‑off.

---

## 6) Wire the full pipeline

**Commands (repo root):**

```bash
# Generate (models + frontend)
dipeo run codegen/diagrams/generate_all --light --debug

# Apply staged backend code
make apply-syntax-only

# Export schema for frontend
python -m dipeo.application.graphql.export_schema apps/server/schema.graphql

# Regenerate frontend TS types & hooks
cd apps/web && pnpm codegen
```

Add these to `make codegen` so it stays one switch.

---

## 7) Tests & guardrails

- Unit test the loader: if no generated files → empty list; with monolith → classes found; with split → classes found.
- Snapshot test: exported `schema.graphql` should include each `*DataType` name.
- Subscription e2e: emit a `EXECUTION_LOG` and assert Apollo client receives a **typed** payload.

---

# Bonus: UI benefits quickly unlocked

- `dipeo/diagram_generated/field-configs.json` can drive dynamic forms in the editor — wire it to existing form components so new node fields appear without handwritten UI.
- With typed subscription payloads, you can replace log JSON parsing in `apps/web/src/domain/execution/hooks/` with direct field access.

---

# Done checklist

-

---

# What to do next if you want to go further

- Generate **event payload types** straight from your `EventType` → Python dataclasses, then Strawberry-`@type` wrap them (so the event union stays in sync automatically).
- If you want `.graphql` sources instead of TS `gql` strings, swap the generator to emit `*.graphql` files per entity and point `apps/web/codegen.yml` at those. The rest of the flow stays the same.

