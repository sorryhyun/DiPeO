# DiPeO (Diagrammed People & Organizations) – Architecture & Flow

*(Refactor branch)*

DiPeO is an open-source platform that lets developers **design, run and monitor multi-agent AI workflows** as diagrams instead of raw code.
The refactor branch reorganises the project into a single **monorepo** and introduces a simpler, container-based dependency-injection system, an end-to-end code-generation pipeline, and a richer memory model for agent conversations.

---

## 1. Repository layout

| Path                      | What it is                                         | Highlights                                                                              |
| ------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **`apps/web`**            | React 19 visual editor                             | Vite, TailwindCSS, @xyflow/react canvas, Apollo + GraphQL, TRPC, TanStack Query, Zustand state |
| **`apps/server`**         | FastAPI / Strawberry-GraphQL backend               | Python 3.13, Hypercorn ASGI, GraphQL subscriptions for live updates                     |
| **`apps/cli`**            | Headless CLI runner                                | `dipeo run diagram.yml`, code-gen helpers                                               |
| **`dipeo/`**              | Core domain + application + infrastructure library | Execution engine, DI containers, adapters, code-gen output                              |
| **`diagram_generated*/`** | Auto-generated code                                | Pydantic models, node handlers, GraphQL schema, TS hooks                                |

---

## 2. High-level architecture

| Layer                        | Purpose                                      | Key tech                                                                                                            |
| ---------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Front-end**<br>`apps/web`  | Drag-and-drop diagram editor, run monitor    | *React 19*, Vite, @xyflow/react, Apollo Client + `graphql-ws`, TRPC, Zustand, TanStack Query, React-Hook-Form, TailwindCSS |
| **Backend**<br>`apps/server` | Exposes GraphQL API, orchestrates runs       | *Python 3.13*, FastAPI, Strawberry GraphQL, GraphQL subscriptions, Hypercorn, Pydantic v2                          |
| **Core library**<br>`dipeo/` | Domain models, execution engine, memory      | Event-driven architecture, async runtime, Pydantic, DI service registry                                             |
| **CLI**<br>`apps/cli`        | Scriptable interface, code-gen driver        | `click`-style UX, pure Python, `requests/pyyaml` only                                                               |

---

## 3. Dependency-injection containers

```text
Top-level Container
├── CoreContainer            # Pure, stateless domain services
├── InfrastructureContainer  # Adapters (LLM, storage, …)
└── ApplicationContainer     # Orchestrators & use-cases
```

* **CoreContainer** – validator, prompt builder, template engine
* **InfrastructureContainer** – storage adapter, LLM adapter (wraps domain LLM service, sources keys from the API-key service), optional Notion / AST adapters (default `None`)
* **ApplicationContainer** – compilation pipeline, diagram converter, conversation & person managers, **`ExecuteDiagramUseCase`**

All three share a single **ServiceRegistry**, making service resolution explicit and testable.

---

## 4. Code-generation pipeline

1. **Define** nodes in TypeScript specs (`*.spec.ts`).
2. **Generate** → staged Pydantic models, JSON schemas & node handlers (`/dipeo/diagram_generated_staged/`).
3. **Apply** staged code with `make apply` → `/dipeo/diagram_generated/` (imported by both web & backend).
4. **Export** GraphQL schema (`make graphql-schema`).
5. **Frontend** runs `pnpm codegen` to produce strongly-typed hooks.

> **Add a new node** → write a TS spec **+** Python handler → run `make codegen` → everything stays in sync.

---

## 5. Memory & conversation model

* Every message goes into a **global, immutable conversation log**.
* Each *person* (LLM instance) views that log through **filters** such as `ALL_INVOLVED`, `SENT_BY_ME`, `CONVERSATION_PAIRS`, `ALL_MESSAGES`, combined with sliding-window limits.
* Memory is configured per job using **Memory Profiles** (`GOLDFISH`, `MINIMAL`, `FOCUSED`, `FULL`) or custom settings, enabling patterns like:

  * **Debates** – judges use `FULL` profile, debaters use `FOCUSED` profile for limited context.
  * **Pipelines** – context gradually shrinks along downstream tasks (from `FULL` → `FOCUSED` → `MINIMAL`).
  * **GOLDFISH** – Complete memory reset between executions for stateless agents.

---

## 6. Execution flow (simplified)

```mermaid
sequenceDiagram
  participant UI
  participant Backend
  participant ExecutionEngine
  participant LLMService
  UI->>Backend: runDiagram(id) via GraphQL
  Backend->>ExecutionEngine: start()
  loop async steps
    ExecutionEngine->>LLMService: complete()
    LLMService-->>ExecutionEngine: result
    ExecutionEngine-->>Backend: event emitted
    Backend-->>UI: GraphQL subscription update
  end
  ExecutionEngine-->>Backend: finished
  Backend-->>UI: completion event via subscription
```

---

## 7. Tech-stack cheat-sheet

| Area             | Tools / libs                                                                                                           |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Languages**    | TypeScript 5 (pnpm + Vite) • Python 3.13                                                                               |
| **Front-end**    | React 19, @xyflow/react, Apollo Client, GraphQL-WS, TRPC, TanStack Query, Zustand, TailwindCSS, Zod                    |
| **Back-end**     | FastAPI, Strawberry GraphQL, Hypercorn, Pydantic v2, Tenacity (retry), AsyncEventBus, Redis (optional for multi-worker)     |
| **DI / IoC**     | Custom service-registry pattern (core / infra / app containers)                                                        |
| **LLM adapters** | OpenAI, Anthropic, Gemini (extensible)                                                                                 |
| **Tooling**      | Ruff, Mypy, Makefile helpers                                                                                           |
| **CI / tests**   | Pytest, Vitest, GitHub Actions (lint, type-check, e2e)                                                                 |

---

## 8. Running & deploying

### Local development

```bash
# one-time setup
make install          # Python & Node deps
# start everything (backend :8000, frontend :3000)
make dev-all
```

> Hot-reload: Vite auto-reloads the UI; restart Hypercorn manually for backend changes.

### Production

* Build SPA: `pnpm build` → serve via CDN or mount under FastAPI.
* Serve API: `hypercorn apps/server.main:app -w 4 -k uvloop` (or Uvicorn/Gunicorn).
* For multi-worker deployments, Redis is required for GraphQL subscriptions to work across workers.
* Container images & Helm charts are provided in `/deploy/`.

### Desktop Application

For standalone Windows installations, use PyInstaller to create `.exe` files from the server and web components. The installer (NSIS) bundles these executables for distribution.

---

## 9. Event-Driven Architecture

The system uses a fully event-driven architecture for execution and monitoring:

* **AsyncEventBus** – Central event distribution with fire-and-forget pattern
* **EventBasedStateStore** – Lock-free state persistence with per-execution caches
* **GraphQL Subscriptions** – Real-time updates to UI (replaced SSE)
* **No Global Locks** – Per-execution isolation enables true parallel execution
* **Event Types** – Standardized events (EXECUTION_STARTED, NODE_COMPLETED, etc.)

This architecture enables:
- Zero-impact monitoring (fire-and-forget events)
- True parallel execution without contention
- Clean separation of concerns via event decoupling
- Asynchronous state persistence

## 10. Why the refactor matters 🌟

* **Single service registry** → no hidden globals, easier tests.
* **Unified code-gen** → one source of truth for types across TS & Python.
* **Memory filters** → flexible multi-agent patterns without per-agent silos.
* **Three-container DI** → swap infra (LLM, storage) without touching domain logic.
* **Event-driven design** → True parallel execution without global locks.
* **Monorepo discipline** → atomic changes across web, server, and CLI.
