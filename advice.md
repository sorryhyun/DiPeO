Your analysis is solid—and you’ve basically converged on the right target: keep wrappers for mutations, return direct types for queries, and normalize names. The part I’d improve is **how** you get there without hand-maintaining `application/graphql/schema/*`. You can push this entirely into the generator so the runtime schema matches the frontend with **zero** manual glue, and you also get a safe deprecation story for the older `get_*`/`list_*` fields.

Here’s a crisp plan that matches the current codebase structure you’ve got (`projects/codegen/...`, `diagram_generated/graphql/*`, `application/graphql/*`) and lets you delete almost all of the manual query code.

---

# What to change (high level)

1. **Hybrid-by-default in codegen**

   * **Queries** → return direct types (`ExecutionStateType`, `DomainDiagramType`, …) and expose **noun** field names (`execution`, `executions`, `diagram`, `diagrams`, `person`, `persons`, …).
   * **Mutations** → keep `*Result` envelopes.
   * **Subscriptions** → unchanged.

2. **Automatic backward-compat aliases (generated)**

   * For every query named `get_X`/`list_Xs`, generate **two** fields:

     * a deprecated legacy field (`get_execution`, `list_executions`)
     * a preferred alias without the verb (`execution`, `executions`)
   * Both call the same resolver implementation; no duplicate logic.

3. **Result types cleanup**

   * Keep only a single data slot (`data`) in `*Result`. Keep the entity-specific field (`execution`, `diagram`, …) **but mark it deprecated** so the schema still works for any caller expecting the old shape.

4. **Delete manual Query class**

   * With the above, `application/graphql/schema/queries.py` becomes unnecessary. Keep your `schema_factory.py` using the generated `Query/Mutation/Subscription`.

---

# Minimal patchset (fits your repo)

### 1) Teach the extractor to produce hybrid return types + aliases

File: `projects/codegen/code/backend/strawberry_schema_extractor.py`

* Change return type mapping so **queries** get direct types and **mutations** keep envelopes.
* Also compute a preferred, verb-less field name for queries.

```diff
@@
-def get_return_type(operation_name: str) -> str:
+def get_return_type(operation_name: str, operation_type: str) -> str:
     """
-    Map operation names to their correct return types.
-    Based on the resolvers in dipeo/application/graphql/schema/mutations/
+    Map operation names to GraphQL return types.
+    Queries → direct types, Mutations → Result envelopes.
     """
+    DIRECT = {
+        "Diagram": "DomainDiagramType",
+        "Execution": "ExecutionStateType",
+        "Person": "DomainPersonType",
+        "ApiKey": "DomainApiKeyType",
+        "Provider": "ProviderType",
+        "OperationSchema": "OperationSchemaType",
+        "CliSession": "CliSession",  # already defined in application/graphql/types
+        "File": "JSON",  # structured later if needed
+        "SystemInfo": "JSON",
+        "ProviderStatistics": "ProviderStatisticsType",
+    }
+
+    def list_of(t: str) -> str:
+        return f"list[{t}]"
+
+    # Queries: infer entity from the op name and return direct types
+    if operation_type == "query":
+        if operation_name.startswith("Get"):
+            entity = operation_name[3:]          # GetExecution → Execution
+            base = DIRECT.get(entity, "JSON")
+            return base
+        if operation_name.startswith("List"):
+            entity = operation_name[4:]         # ListExecutions → Executions
+            entity = entity[:-1] if entity.endswith("s") else entity
+            base = DIRECT.get(entity, "JSON")
+            return list_of(base)
+
+    # Mutations (and anything unknown): keep envelopes (existing mappings below)
@@
-            return 'ExecutionResult'
+            return 'ExecutionResult'
@@
-            return 'DiagramResult'
+            return 'DiagramResult'
@@
-        return 'JSON'
+        return 'JSON'
@@
-                return_type = get_return_type(operation_name)
+                return_type = get_return_type(operation_name, operation_type)
+                alias_name = None
+                if operation_type == "query":
+                    # Prefer noun forms: get_execution → execution, list_executions → executions
+                    snake = camel_to_snake(operation_name)
+                    if snake.startswith("get_"):
+                        alias_name = snake[4:]
+                    elif snake.startswith("list_"):
+                        alias_name = snake[5:]
+
+                operation_info = {
+                    "operation_name": operation_name,
+                    "operation_type": operation_type,
+                    "field_name": camel_to_snake(operation_name),
+                    "alias_name": alias_name,
+                    "return_type": return_type,
+                    "parameters": extract_parameters(obj),
+                }
```

> This gives the template everything it needs: `field_name`, optional `alias_name`, `return_type`, and the parameters, with **queries returning direct types**.

---

### 2) Generate noun fields + legacy aliases

File: `projects/codegen/templates/strawberry/strawberry_schema_from_operations.j2`

Add alias field generation and mark the legacy `get_/list_` fields as deprecated.

```diff
@@ class Query:
-    @strawberry.field
-    async def {{ operation.field_name }}(
+    @strawberry.field{% if operation.alias_name %}(deprecation_reason="Use '{{ operation.alias_name }}' instead"){% endif %}
+    async def {{ operation.field_name }}(
         self,
         info: Info{% if operation.parameters %},{% endif %}
         {% for param in operation.parameters %}
         {{ param.name }}: {{ param.type }}{% if not loop.last %},{% endif %}
         {% endfor %}
     ) -> {{ operation.return_type }}:
@@
         return await executor.execute("{{ operation.operation_name }}", variables=variables)
+
+    {% if operation.alias_name %}
+    # Back-compat preferred alias without 'get_'/'list_'
+    @strawberry.field(name="{{ operation.alias_name }}")
+    async def {{ operation.alias_name }}(
+        self,
+        info: Info{% if operation.parameters %},{% endif %}
+        {% for param in operation.parameters %}
+        {{ param.name }}: {{ param.type }}{% if not loop.last %},{% endif %}
+        {% endfor %}
+    ) -> {{ operation.return_type }}:
+        return await self.{{ operation.field_name }}(info{% if operation.parameters %}, {{ operation.parameters | map(attribute='name') | join(', ') }}{% endif %})
+    {% endif %}
```

> Now your generated `Query` exposes both `get_execution` (**deprecated**) and `execution` (**preferred**) and returns a **direct** `ExecutionStateType`.

---

### 3) Deprecate duplicate entity fields in `*Result` types

File: `projects/codegen/templates/strawberry/strawberry_results.j2`

Replace the second, entity-specific field with a deprecated field so callers can transition to `data` cleanly. Example shown here for `ExecutionResult` (apply the same to Diagram/Person/ApiKey):

```diff
@@ class ExecutionResult(BaseResultMixin):
-    data: Optional[ExecutionStateType] = None
-    execution: Optional[ExecutionStateType] = None
+    data: Optional[ExecutionStateType] = None
+    # Back-compat (prefer `data`)
+    execution: Optional[ExecutionStateType] = strawberry.field(default=None, deprecation_reason="Use 'data'")
```

(Do the same pattern for `diagram`, `person`, `api_key`, etc., where present.)

---

### 4) Schema factory stays simple

`application/graphql/schema_factory.py` is already importing from `dipeo.diagram_generated.graphql.generated_schema`. Leave it that way. With the changes above, you can remove the manual `application/graphql/schema/queries.py` after verification.

---

# Why this is better than “manual hybrid”

* **One source of truth**: the generator now emits the public API you want. No more drift between generated and hand-rolled schema.
* **Zero breaking changes**: old `get_*`/`list_*` fields still exist (deprecated) and return the same shapes as the new noun fields.
* **Frontend already matches**: your web app’s generated ops are using `execution(...) { ... }` etc., so no churn there.
* **Cleaner envelopes**: `*Result` keeps a single `data` slot; entity-named fields are still there but emit deprecation warnings in introspection.

---

# Rollout checklist

1. Apply the patches above.
2. Regenerate:

   ```
   make graphql-schema
   ```
3. Smoke test a few queries/mutations against the running server:

   * `execution(id: "...") { id status }`  ✅
   * `get_execution(id: "...") { id status }`  ✅ (works but marked deprecated)
   * `execute_diagram(input: ...) { success error data { id status } }`  ✅
4. Remove `application/graphql/schema/queries.py` (and any imports of it) once you confirm parity.
5. Keep the deprecations for at least one release. Add a note in `docs/` with the replacement fields.

---

# Extra polish (optional, low effort)

* **Nullability**: Prefer nullable top-level query returns for “not found” (`ExecutionStateType` vs `ExecutionStateType!`). If you’d rather 404 via GraphQL errors, raise `GraphQLError(..., extensions={"code":"NOT_FOUND"})` in your resolvers.
* **Pagination**: When you’re ready, upgrade list queries to Relay connections. For now, the `list[...]` approach is fine and matches your current frontend.
* **JSON vs typed**: Keep JSON only for truly dynamic shapes (`system_info`, `prompt_file`, etc.). Where fixed, generate minimal types (you already have `ProviderType`, `OperationSchemaType`, etc.).

If you want, I can also hand you a tiny codemod to auto-replace any lingering frontend uses of `get_*` or wrapper access with the new noun forms—but with the deprecation path above, you shouldn’t need it.
