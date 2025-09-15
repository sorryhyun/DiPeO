Great audits. Here’s a concrete, code-first adoption plan mapped to the current DiPeO tree (monorepo, refactor branch). I’ve kept each item scoped, with exact files to touch, config knobs to add, and a lightweight test plan so you can land these incrementally without churn.

---

# Medium priority (operability & guard-rails)

## 1) Global DI overrides have no safety rails

**Problem**: `ServiceRegistry.register()` silently replaces bindings. That’s nice for tests, dangerous in prod.

**What to change**

* Add an “environment & freeze” model to the registry so overrides require an explicit switch and are forbidden once bootstrapping ends.

**Files**

* `dipeo/application/registry/service_registry.py`
* `dipeo/config/settings.py` (new flags)

**Suggested code**

```python
# dipeo/config/settings.py
class AppSettings(BaseSettings):
    # ...
    env: str = Field(default="dev", env="DIPEO_ENV")  # dev|test|prod
    di_allow_override: bool = Field(default=False, env="DIPEO_DI_ALLOW_OVERRIDE")
    di_freeze_after_boot: bool = Field(default=True, env="DIPEO_DI_FREEZE_AFTER_BOOT")
```

```python
# dipeo/application/registry/service_registry.py
class ServiceRegistry:
    def __init__(self, *, allow_override: bool | None = None):
        from dipeo.config import get_settings
        self._services: dict[str, object] = {}
        self._factories: dict[str, Callable[[], object]] = {}
        self._lock = threading.RLock()
        self._resolve_hits: dict[str, int] = {}
        self._frozen = False
        settings = get_settings()
        self._allow_override = (
            settings.di_allow_override or (settings.env in {"dev", "test"})
            if allow_override is None else allow_override
        )

    def freeze(self) -> None:
        with self._lock:
            self._frozen = True

    def register(self, key: ServiceKey[T], service: T | Callable[[], T], *, override: bool = False) -> None:
        with self._lock:
            exists = key.name in self._services or key.name in self._factories
            if self._frozen and exists and not override:
                raise RuntimeError(f"DI is frozen; refusing to rebind {key!r}")
            if exists and not (override or self._allow_override):
                raise RuntimeError(f"Refusing to overwrite binding for {key!r} without override=True")

            if callable(service) and not hasattr(service, "__self__"):
                self._factories[key.name] = service
                self._services.pop(key.name, None)
            else:
                self._services[key.name] = service
                self._factories.pop(key.name, None)

    def override(self, key: ServiceKey[T], service: T | Callable[[], T]) -> None:
        self.register(key, service, override=True)
```

**Bootstrap integration**

* Freeze after wiring completes:

  * `dipeo/application/bootstrap/application_container.py` → end of `_setup_application_services()` call `self.registry.freeze()`.
  * Server: during startup, after containers are initialized, call `registry.freeze()` (see `apps/server/main.py` lifespan).
  * CLI: after `init_resources(container)` (see `apps/cli` entry), freeze.

**Test plan**

* Unit: registering twice without `override=True` raises in `prod`.
* Unit: child registry can still shadow parent during tests when `DIPEO_ENV=test`.
* Integration: server boots with `DIPEO_ENV=prod` and **fails fast** if any late override is attempted.

---

## 2) Lifecycle/teardown holes

**Problem**: No unified shutdown loop; some resources depend on process exit (e.g., Claude sessions, Redis connections).

**What to add**

* A tiny, explicit lifecycle manager that calls `initialize()` and `shutdown()` for every service implementing `Lifecycle` (you already have `dipeo/application/bootstrap/lifecycle.py` protocols; let’s wire them through).

**Files**

* `dipeo/application/bootstrap/containers.py` (ensure `Container.initialize()/shutdown()` collect & run lifecycles)
* `dipeo/application/bootstrap/infrastructure_container.py` and `.../application_container.py` (register lifecycle services)
* Providers:

  * `dipeo/infrastructure/llm/providers/claude_code/transport/session_pool.py` → implement `Lifecycle` (idempotent `initialize()`, graceful `shutdown()` disconnecting sessions).
  * `dipeo/infrastructure/execution/messaging/message_router.py` and `.../redis_message_router.py` → implement `Lifecycle` (start background health loop if any; close redis/publish tasks).
  * Any open file/db clients (e.g., `integrations/*`) to implement `ShutdownOnly` at least.

**Glue**

* Server lifespan (already imports `init_resources`/`shutdown_resources`): verify it calls `await container.initialize()` (which should in turn call `initialize_service(...)` for all known singletons), and on shutdown calls `await container.shutdown()` in **reverse registration order**.

**Test plan**

* Unit: `Lifecycle` methods called exactly once; shutdown tolerates exceptions and continues others.
* Integration: start server, open a Claude session (log confirms), stop server, logs show session pool drained and redis connections closed.
* CLI: run/interrupt; confirm graceful teardown runs on `SIGINT/SIGTERM`.

---

## 3) Event backpressure can drop updates

**Problem**: Bounded per-connection queues + in-memory buffers → bursts drop messages; clients must poll to recover.

**Incremental fix (fast)**

* **Server-side replay buffer with sequence IDs**:

  * In `dipeo/infrastructure/execution/messaging/message_router.py`:

    * Stamp each broadcast with a monotonically increasing `seq` per `execution_id` and keep a ring buffer (`deque(maxlen=buffer_max_per_exec)`).
    * On subscription, accept `last_seq` (or `None`) from the GQL resolver (extend `application/graphql/schema/base_subscription_resolver.py` to pull an optional `lastSeq` argument) and replay any missed events synchronously before streaming live.
  * Expose `dropped_count` metrics per connection; log when applying backpressure.
* **Config knobs** (already present): `DIPEO_MSG_BUFFER_MAX`, `DIPEO_MSG_BUFFER_TTL`. Enforce TTL prune on a timer (there is a `_cleanup_old_buffers`; ensure it’s scheduled).

**Robust fix (recommended)**

* **Switch fan-out to Redis Streams (not Pub/Sub) for durability and consumer backpressure**:

  * Create `RedisStreamsMessageRouter` in `dipeo/infrastructure/execution/messaging/redis_streams_message_router.py`.
  * Per execution stream key: `exec:{execution_id}:events`.
  * Producer: `XADD` with `MAXLEN ~ N` (configurable), payload includes `seq`, `type`, `ts`.
  * Per GraphQL connection: consumer group `cg:exec:{execution_id}`, consumer name `conn:{connection_id}`; read with `XREADGROUP`, ack with `XACK`.
  * On (re)subscribe with `last_id`, start from there; otherwise `$` (only new).
  * Background task to `XTRIM` and a nightly job to delete stale streams for completed executions (TTL).
* Keep `in_memory_event_bus` for single-process dev; auto-select Redis Streams router when `settings.messaging.redis_url` is set or `WORKERS>1`.

**GraphQL changes**

* `application/graphql/schema/base_subscription_resolver.py`:

  * Add optional arg `lastSeq: Int` (or `lastId: String` for Streams).
  * On subscribe, call `message_router.subscribe_connection_to_execution(...)` with that offset so the router can replay (in-mem) or attach to streams (Redis).
  * Continue to send `KEEPALIVE` events; they can carry the latest committed `seq`.

**Test plan**

* Load test: burst 1k events in 200 ms → confirm **no loss** with Streams, and with in-mem ring buffer you can replay last N.
* Kill & restart a GraphQL worker: client reconnects with `lastId` → receives gap replay.
* Metrics endpoint exposes `pending`, `dropped`, `avg_latency` per connection.

**Rollout**

* Phase 1 (today): in-mem replay + sequence IDs (minimal code, big UX win).
* Phase 2: Redis Streams behind a feature flag `DIPEO_MSG_BACKEND=streams`.

---

# Medium–low priority (architecture hygiene & data retention)

## 4) Cross-layer base class leak

**Problem**: A “BaseService”-style inheritance bleeding across layers (domain ↔ app ↔ infra). Your repo already has `dipeo/domain/base/mixins.py`—let’s finish the job and delete the inheritance pattern entirely.

**Steps**

1. **Inventory**: grep for any inheritance from a cross-layer base (e.g., `class X(BaseService)`).
2. **Replace** with targeted mixins from `domain/base/mixins.py`:

   * `LoggingMixin` for logger,
   * `ValidatedMixin` (if you have it) for input validation,
   * `TimedOperationMixin` (or similar) for timing/metrics.
3. **Constructor shape**: keep CTOR signatures minimal; depend on **ports** not concrete adapters (the refactor already heads this direction).
4. **Wire** via DI keys from `dipeo/application/registry/keys.py`; avoid importing application services into domain.
5. **Delete the base** once no subclass remains. Add a lint rule:

   * A simple ruff custom rule or CI grep that fails on `class .*BaseService`.

**Data retention angle**

* For events and messages, set explicit retention:

  * In-mem buffers: `DIPEO_MSG_BUFFER_TTL` already exists. Ensure GC actually runs periodically.
  * Redis Streams: set `MAXLEN ~ N` and expire stream keys (e.g., keep 24–48h post-completion) with a small janitor task in server lifespan shutdown or a periodic job.

**Test plan**

* Type check (mypy) to ensure domain depends only on ports.
* Unit tests for services now importing only mixins/ports from domain.

---

## Small but valuable extras you’ll get “for free”

* **DI auditability**: add `list_services()` (exists) + `report_unused()` (exists) to a debug endpoint so you can spot dead bindings. Fail CI if critical bindings are unused.
* **Safer keys**: allow “final” keys that can’t be overridden even in dev:

  ```python
  @dataclass(frozen=True, slots=True)
  class ServiceKey[T]:
      name: str
      final: bool = False
  # register() blocks override if key.final is True (unless DIPEO_ENV=test)
  ```
* **Backpressure visibility**: expose `message_router.get_stats()` on a `/system/metrics` route (server) and surface a tiny “subscriptions health” widget in the web app (you already compute latency/queue size).

---

# Acceptance checklist (ship this in PRs)

* [ ] Registry refuses silent overrides in prod; registry frozen after boot.
* [ ] Lifespan hooks call initialize/shutdown across services; Claude sessions/Redis closed gracefully.
* [ ] Event router supports replay (seq or streams); no silent drops under bursts; metrics exposed.
* [ ] No inheritance from cross-layer base classes; mixins/ports only.
* [ ] Retention policies documented (`MAXLEN`, TTLs) and enforced.

If you want, I can draft the exact diffs for the registry, the in-mem replay (sequence ID + ring buffer), and a minimal Redis Streams router skeleton next.
