Below is a concise refactor roadmap focused on **eliminating duplication, tightening error-handling, and making each handler smaller and easier to test**.  The steps are ordered so you can harvest the “low-hanging fruit” first, then converge on deeper architectural changes.

---

### 1 – Quick wins (≤ 1 day)

| Goal                                               | What to change                                                                                                                                                                                                                                                                                                                                                                                | Why                                                               |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| **Centralise repeated helpers**                    | Create `executors/handler_utils.py` with:<br>• `process_inputs()` – one canonical version of the logic that strips Person-Job metadata (now lives in both Notion & DB handlers) <br>• `substitute_variables()` – thin wrapper around existing `executor_utils.substitute_variables` but also supports `$var` (duplicated in `job_handler`) <br>• `get_api_key()` (appears in Notion handler)  | Removes 80+ lines across the six files; gives one tested surface. |
| **Dictionary dispatch instead of if/elif ladders** | Replace the operation chains in `notion_handler` and `db_handler` with a simple `dict[Enum] → coroutine` map. Same for `job_handler` language switch.                                                                                                                                                                                                                                         | Leaner, O(1) lookup, easier to extend, auto-inspected in tests.   |
| **Consistent logging helper**                      | Provide `log_action(logger, node_id, action, **extra)`; call it everywhere instead of ad-hoc `logger.info(...)`.                                                                                                                                                                                                                                                                              | Log format becomes uniform; filtering is easier.                  |
| **Reuse a `safe_eval` util**                       | Move `_safe_eval` out of `condition_handler` into `handler_utils`.                                                                                                                                                                                                                                                                                                                            | Makes it testable in isolation and reusable in future nodes.      |

---

### 2 – Shared execution wrapper (1–2 days)

1. **Introduce `BaseNodeHandler` (simple mix-in)**

   ```python
   class BaseNodeHandler:
       async def exec(self, ctx, props, inputs, services):
           try:
               result = await self.run(ctx, props, inputs, services)
               return NodeOutput(value=result["value"], metadata=result.get("meta", {}))
           except Exception as exc:
               logger.exception("%s failed", self.__class__.__name__)
               raise RuntimeError(str(exc)) from exc
   ```

   Each concrete handler implements a narrow `run()`; boiler-plate try/except, timing, and metadata building disappear from the current handlers (≈40–60 lines each).

2. **Decorator upgrade** – have `@node` wrap the handler class, inject the mix-in, and still register metadata.

Result: every handler file shrinks to “business logic only”.

---

### 3 – Unify sandboxed code execution (2–3 days)

Current sandboxes live in **two places**:

* `_execute_code` inside `db_handler` (inline exec with extremely tight builtin-allow-list)&#x20;
* language-specific `_exec_python/_exec_js/_exec_bash` in `job_handler` (temp-file + subprocess)&#x20;

Refactor plan:

| Step    | Action                                                                                                                                              |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **3.1** | Create `executor_sandbox.py` housing a **single** async `run_code(language, code, inputs, timeout)` that internally dispatches to language modules. |
| **3.2** | Move both handlers to call this sandbox.                                                                                                            |
| **3.3** | Consolidate duplicate helper (`_try_json`) and env/IO helpers into that file.                                                                       |

Benefits: identical timeout/error semantics, one test surface for security hardening, easy addition of e.g., Ruby or Go.

---

### 4 – Metadata & token-usage normalisation (1 day)

* In `person_job_handler` you build rich metadata with token usage; other handlers build ad-hoc dicts.
  **Create a dataclass `ExecutionMeta`** (with `.to_dict()`) that all handlers fill incrementally (start time → end time etc.).
* Update `BaseNodeHandler` to call `ExecutionMeta.finish()` automatically.

---

### 5 – Stronger typing + tests (parallel, 2 days)

1. Turn on **`mypy --strict`** for `executors/` and gradually add missing type hints (easy once helpers are centralised).
2. Add unit tests for:

   * `handler_utils.process_inputs` (covers PersonJob output stripping)
   * `safe_eval`
   * `executor_sandbox.run_code` happy path / timeout / bad-code paths

---

### 6 – Stretch goals (post-refactor)

| Idea                                                                                                                                                                  | Pay-off                       |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| **Dependency-Injection container** (e.g. `wired` or `punq`) so handlers ask for `services.get(...)` less often – constructor already guarantees it.                   | Cleaner code, easier mocking. |
| **GraphQL resolver reuse** – once GraphQL migration is complete, expose handlers as root resolvers; each already returns data & metadata in a GraphQL-friendly shape. |                               |
| **Code-gen handler skeleton** – a `pnpm generate:handler` (or cookiecutter) that pre-fills the new pattern to keep future code DRY.                                   |                               |

---

## Recommended execution order

1. **Helpers & quick wins**
2. **BaseNodeHandler + decorator patch**
3. **Sandbox consolidation**
4. **Metadata unification**
5. **Type-safety and tests**

Each stage leaves the repo in a compiling, passing-tests state; you can merge incrementally without long-lived branches.

---

### Deliverables

| Milestone | Branch                       | PR contents                                                |
| --------- | ---------------------------- | ---------------------------------------------------------- |
| v1.1      | `refactor/handlers-helpers`  | `handler_utils.py`, duplicate code removal                 |
| v1.2      | `refactor/base-node-handler` | mix-in, decorator, handler rewrites                        |
| v1.3      | `refactor/sandbox-unify`     | `executor_sandbox.py`, updated `db_handler`, `job_handler` |
| v1.4      | `refactor/metadata`          | `ExecutionMeta`, unified metadata                          |
| v1.5      | `chore/types-tests`          | mypy config, new pytest suites                             |

By the end of **v1.5** each `_handler.py` shrinks by roughly 30-50 %, test coverage climbs, and adding a brand-new node becomes a \~50-line task instead of re-copying 150 lines of boiler-plate.
