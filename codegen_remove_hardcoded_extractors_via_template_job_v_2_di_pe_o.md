# Goal

Eliminate most hardcoded codegen logic and per-purpose “extractor” nodes by slightly enhancing `template_job` and shifting AST → output shaping into templates + filters. Keep the pipeline dog-fooded (Light YAML), but cut 30–50% of codegen nodes and Python glue.

---

## TL;DR – What we’ll change

1. ``** v2** (small, targeted upgrades)

- **foreach**: render one template N times over an array and write to per-item paths
- **path templating**: allow `output_path` (or `foreach.output_path`) to be a template string
- **preprocessor (optional)**: (module\:function) that returns a context dict → avoids bespoke extractor nodes when needed
- **variables**: allow dotted-path picks and small expressions (re-using existing simple template processor) so we can wire inputs without an extra `code_job` joiner

2. **Jinja filters/macros** (no breaking changes)

- Add a tiny **AST helper pack** registered in the existing Jinja filter registry so templates can ask the cached TS AST for:
  - `ts_consts(ast, name)` → constant value (e.g., `NODE_TYPE_MAP`)
  - `ts_iface(ast, name)` → interface by name
  - `ts_specs(ast)` → array of detected Node specs (generic, not node-type hardcoded)

3. **Diagrams**

- Replace many `…extract_*.py` steps with **one** `template_job` per artifact group (models, enums, schema, frontend, queries).
- Keep the early **“Parse All TypeScript”** + **“Load AST Cache”** step. Everything after becomes templates.

4. **Source of truth**

- Keep TypeScript specs as SoT. No more extra per-artifact Python shapers.

---

## Inventory – current hardcoded spots to retire

> These are present in your repo and can be consolidated away.

- `projects/codegen/code/shared/typescript_spec_parser.py` — hand-picks constants/spec names
- `projects/codegen/code/shared/simplified_extractors.py` — multiple outputs (node specs, strawberry, models) from AST (still custom logic per artifact)
- `projects/codegen/code/models/conversions_extractor_v2.py` — special-case `NODE_TYPE_MAP` parsing
- `projects/codegen/code/frontend/frontend_node_extractor.py` — bespoke frontend shaping
- `projects/codegen/code/frontend/prepare_query_data.py` — custom query mapping

These exist mostly to: (a) normalize AST values, (b) fan-out over specs, (c) format file paths. All three can be handled generically by **foreach + filters + path templating**.

---

## `template_job` v2 – minimal API additions

### TypeScript model (source of truth)

`dipeo/models/src/core/nodes/template-job.data.ts`

```ts
export interface TemplateJobNodeData extends BaseNodeData {
  template_path?: string;
  template_content?: string;
  /** Single-file path; can contain template expressions */
  output_path?: string;
  /** Simple key→value map passed to template; string values are resolved */
  variables?: JsonDict;
  engine?: TemplateEngine;

  /** Render a template for each item and write many files */
  foreach?: {
    /** Array or dotted-path string to an array in inputs */
    items: unknown[] | string;
    /** Variable name to expose each item under in the template (default: "item") */
    as?: string;
    /** File path template, e.g. "dipeo/diagram_generated_staged/models/{{ item.nodeTypeSnake }}.py" */
    output_path: string;
    /** Optional: limit, parallel write hint (ignored in v1) */
    limit?: number;
  };

  /** Optional Python preprocessor that returns extra context for the template */
  preprocessor?: {
    module: string;         // e.g. "projects.codegen.code.shared.context_builders"
    function: string;       // e.g. "build_context_from_ast"
    args?: JsonDict;        // passed through as kwargs
  };
}
```

### Handler changes (Python)

`dipeo/application/execution/handlers/template_job.py`

Key points (pseudocode-like diff):

```py
class TemplateJobNodeHandler(TypedNodeHandler[TemplateJobNode]):
    async def run(self, inputs: dict[str, Envelope], request: ExecutionRequest):
        cfg = request.node.props
        ctx = self._collect_base_context(inputs, cfg)

        # (1) optional preprocessor
        if cfg.preprocessor:
            mod = import_module(cfg.preprocessor.module)
            fn = getattr(mod, cfg.preprocessor.function)
            extra = fn(context=ctx, **(cfg.preprocessor.args or {}))
            if isinstance(extra, dict):
                ctx.update(extra)

        # (2) choose engine
        renderer = self._get_jinja_renderer(cfg.template_path, cfg.engine)

        def render_to_path(path_tmpl: str, local_ctx: dict):
            path = renderer.render_string(path_tmpl, **local_ctx)  # path templating
            content = renderer.render(**local_ctx)
            self._write_file(path, content)
            return path

        # (3) foreach fan-out
        if cfg.foreach:
            items = cfg.foreach.items
            if isinstance(items, str):
                items = self._resolve_path_or_expr(items, ctx)  # dotted path / string expr → any
            items = list(items or [])
            if cfg.foreach.limit:
                items = items[: cfg.foreach.limit]
            var_name = cfg.foreach.as or "item"
            written = []
            for item in items:
                local_ctx = {**ctx, var_name: item}
                written.append(render_to_path(cfg.foreach.output_path, local_ctx))
            return EnvelopeFactory.json({"written": written})

        # (4) single-file mode (backward compatible)
        output_path = cfg.output_path or "files/generated/out.txt"
        path = render_to_path(output_path, ctx)
        return EnvelopeFactory.text(path)
```

### Template service additions (tiny)

- **Add helpers as filters** (no API change):
  - `ts_consts(ast, name)` → object|array|string
  - `ts_iface(ast, name)` → interface dict (props, docs)
  - `ts_specs(ast)` → returns the list of node specs (detect `*Spec` constants with `nodeType`)

These sit in `dipeo/infrastructure/services/jinja_template/filters/typescript_filters.py` and are registered in `filters/registry.py` under a new source tag, e.g. `"typescript_ast"`.

> We already have a rich filter registry; we’re only adding 3 helpers.

---

## Replace extractors with 1–2 `template_job`s

### Before (models – typical today)

```
Parse TS → Load AST Cache → Extract Raw Model Data (code_job) → Render Models (template_job)
```

### After (models)

```
Parse TS → Load AST Cache → Render Models (template_job with foreach)
```

**Example node** (drop-in)

```yaml
- label: Render Python Models (foreach)
  type: template_job
  props:
    engine: jinja2
    template_path: projects/codegen/templates/backend/pydantic_single_model.j2
    foreach:
      items: ast_cache | ts_specs     # dotted-path or small expr, see below
      as: spec
      output_path: dipeo/diagram_generated_staged/models/{{ spec.nodeTypeSnake }}.py
    variables:
      ast_cache: "{{ ast_cache }}"   # passes the full AST cache
```

> **How does **``** work?** Two options:
>
> 1. Keep `items: "ast_cache"` and call `ts_specs(ast_cache)` inside the template’s `{% for spec in ts_specs(ast_cache) %}` (multi-file still needs foreach, so we prefer #2), or
> 2. Support a tiny expression resolver in handler (reuse our simple processor) to run pipe-style filters that exist in the registry.
>
> The diff below shows variant (1) which needs **no** new expression resolver.

---

## Template snippets (no more hardcoding)

### `pydantic_single_model.j2` (simplified example)

```jinja
{% set iface = ts_iface(ast_cache, spec.interfaceName) %}
from pydantic import BaseModel

class {{ spec.nodeTypePascal }}NodeData(BaseModel):
{% for p in iface.properties %}
    {{ p.name }}: {{ ts_to_python_type(p.type, p.name) }}{% if p.required is not sameas true %} | None = None{% endif %}
{% endfor %}
```

### `enums.j2` (no conversions extractor)

```jinja
{% set node_type_map = ts_consts(ast_cache, 'NODE_TYPE_MAP') %}
from enum import Enum
class NodeType(str, Enum):
{% for key, val in node_type_map.items() %}
    {{ key|upper }} = "{{ val.split('.')[-1] if '.' in val else val }}"
{% endfor %}
```

### `graphql_schema_v2.j2` (sketch – still pure template)

```jinja
# pull whatever you need from AST
{% set exec_defs = ts_consts(ast_cache, 'executionQueries') %}
# …render
```

---

## Concrete file changes (diff-style)

### 1) Extend Template node data (TS SoT)

`dipeo/models/src/core/nodes/template-job.data.ts`

```diff
 export interface TemplateJobNodeData extends BaseNodeData {
   template_path?: string;
   template_content?: string;
   output_path?: string;
   variables?: JsonDict;
   engine?: TemplateEngine;
+  foreach?: {
+    items: unknown[] | string;
+    as?: string;
+    output_path: string;
+    limit?: number;
+  };
+  preprocessor?: {
+    module: string;
+    function: string;
+    args?: JsonDict;
+  };
 }
```

> Run:
>
> ```bash
> dipeo run codegen/diagrams/generate_all --light --debug
> make apply-syntax-only && make graphql-schema
> ```

### 2) Handler minimal changes

`dipeo/application/execution/handlers/template_job.py` (key excerpts)

```diff
@@ class TemplateJobNodeHandler:
-        output_path = cfg.output_path or "files/generated/out.txt"
-        content = renderer.render(**ctx)
-        self._write_file(output_path, content)
-        return EnvelopeFactory.text(output_path)
+        if cfg.foreach:
+            items = cfg.foreach.items
+            if isinstance(items, str):
+                items = self._resolve_path(items, ctx)
+            items = list(items or [])
+            var = cfg.foreach.as or "item"
+            written = []
+            for it in items[: (cfg.foreach.limit or len(items)) ]:
+                local_ctx = {**ctx, var: it}
+                out = renderer.render_string(cfg.foreach.output_path, **local_ctx)
+                content = renderer.render(**local_ctx)
+                self._write_file(out, content)
+                written.append(out)
+            return EnvelopeFactory.json({"written": written})
+        # single-file mode (back-compat)
+        output_path = renderer.render_string(cfg.output_path or "files/generated/out.txt", **ctx)
+        content = renderer.render(**ctx)
+        self._write_file(output_path, content)
+        return EnvelopeFactory.text(output_path)
```

Add two tiny helpers inside the handler (or reuse TemplateService):

```py
def _resolve_path(self, dotted: str, ctx: dict):
    # supports "a.b.c" lookups into ctx (no new dependency)
    cur = ctx
    for part in dotted.split('.'):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            cur = getattr(cur, part, None)
    return cur
```

### 3) Register TS AST helper filters

`dipeo/infrastructure/services/jinja_template/filters/typescript_filters.py`

```diff
+def ts_consts(ast_cache: dict, name: str):
+    for fpath, ast in (ast_cache or {}).items():
+        for c in (ast.get('constants') or []):
+            if c.get('name') == name:
+                return c.get('value')
+    return None
+
+def ts_iface(ast_cache: dict, name: str):
+    for fpath, ast in (ast_cache or {}).items():
+        for i in (ast.get('interfaces') or []):
+            if i.get('name') == name:
+                return i
+    return None
+
+def ts_specs(ast_cache: dict):
+    specs = []
+    for fpath, ast in (ast_cache or {}).items():
+        for c in (ast.get('constants') or []):
+            val = c.get('value')
+            if isinstance(val, dict) and 'nodeType' in val:
+                specs.append(val)
+    return specs
```

And register in `filters/registry.py`:

```diff
 filter_registry.register('ts_consts', ts_consts, source='typescript_ast')
 filter_registry.register('ts_iface', ts_iface, source='typescript_ast')
 filter_registry.register('ts_specs', ts_specs, source='typescript_ast')
```

> No extractor modules touched; they can be removed after templates are migrated.

---

## Diagram replacements (examples)

### Python models

```yaml
- label: Render Models
  type: template_job
  props:
    engine: jinja2
    template_path: projects/codegen/templates/backend/pydantic_single_model.j2
    foreach:
      items: ast_cache  # iterate in-template via ts_specs(ast_cache)
      as: spec
      output_path: dipeo/diagram_generated_staged/models/{{ spec.nodeTypeSnake }}.py
    variables:
      ast_cache: "{{ ast_cache }}"
```

### Enums

```yaml
- label: Render Enums
  type: template_job
  props:
    engine: jinja2
    template_path: projects/codegen/templates/models/enums.j2
    output_path: dipeo/diagram_generated_staged/enums.py
    variables:
      ast_cache: "{{ ast_cache }}"
```

### Frontend node configs (single template, foreach)

```yaml
- label: Render Frontend Node Configs
  type: template_job
  props:
    engine: jinja2
    template_path: projects/codegen/templates/frontend/node_config.j2
    foreach:
      items: ast_cache
      as: spec
      output_path: apps/web/src/__generated__/nodes/{{ spec.nodeTypePascal }}.ts
    variables:
      ast_cache: "{{ ast_cache }}"
```

> In the template, compute any derived naming via existing `BaseFilters` (pascal/camel/snake) — no Python shaper.

---

## Cleanup checklist (commit order)

-

---

## Why this is “slight”

- **No breaking changes** for existing `template_job` usages
- Only **two new optional fields** and **3 filters**
- Diagrams get shorter; most change is deletion of glue nodes
- Keeps dog-fooding: still one Light workflow runs the whole pipeline

---

## Risks & mitigations

- **Template path bugs** → We render `output_path` through Jinja before writing; add unit tests for 3–4 common patterns (snake/pascal, nested dirs)
- **AST variance** → Filters are tiny and robust; if a constant isn’t found, they return `None` (templates can `{% if ... %}` guard)
- **Performance** → Foreach writes many files in a single node; if needed, add `limit` or chunking later (non-blocking)

---

## Quick unit tests (sketch)

`tests/template_job/test_foreach.py`

```py
async def test_foreach_renders_many(tmp_path):
    # arrange
    ctx = {"ast_cache": {"a.ts": {"constants": [{"name": "XSpec", "value": {"nodeType": "code_job"}}]}}}
    node = TemplateJobNodeData(
        engine="jinja2",
        template_path="projects/codegen/templates/backend/pydantic_single_model.j2",
        foreach={"items": "ast_cache", "as": "spec", "output_path": str(tmp_path/"{{ spec.nodeType }}.py")},
        variables=ctx,
    )
    # act
    out = await handler.run({"ast_cache": EnvelopeFactory.json(ctx["ast_cache"])}, request)
    # assert
    assert any(p.suffix == ".py" for p in tmp_path.iterdir())
```

---

## Expected impact

- **Delete** 4–6 extractor modules and 6–10 nodes across diagrams
- **Fewer circular/hidden assumptions** (no `DIPEO_BASE_DIR` hacks in extractors)
- **Faster iteration**: new artifact = new template + foreach; *no* new Python

---

## Rollout plan

1. Ship handler + filters behind a feature flag `DIPEO_TEMPLATE_FOREACH=1`
2. Convert **enums** + **models** first (lowest risk)
3. Convert **frontend nodes**, then **GraphQL queries**
4. Remove deprecated extractors in two sprints

---

## Appendix – one-file diagram after refactor (models only)

```yaml
version: light
nodes:
  - {label: Start, type: start}
  - label: Parse All TypeScript
    type: typescript_ast
    props: { source_file: "dipeo/models/src", extract: [interfaces, types, enums, constants] }
  - label: Save AST Cache
    type: db
    props: { operation: write, sub_type: file, file: temp/ast_cache.json }
  - label: Render Models
    type: template_job
    props:
      engine: jinja2
      template_path: projects/codegen/templates/backend/pydantic_single_model.j2
      foreach:
        items: ast_cache
        as: spec
        output_path: dipeo/diagram_generated_staged/models/{{ spec.nodeTypeSnake }}.py
      variables: { ast_cache: "{{ ast_cache }}" }
connections:
  - {from: Parse All TypeScript, to: Render Models, label: ast_cache, content_type: object}
```

