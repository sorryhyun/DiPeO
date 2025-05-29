# DiPeO, Diagrammed People (agents) & Organizations (agent system)
![image info](/img.png)

DiPeO(daɪpiːɔː) is a **monorepo** for building, executing, and monitoring AI‑powered agent workflows through an intuitive visual programming environment. The repository is composed of reusable TypeScript **packages**, a React‑based **frontend**, and a FastAPI **backend** that work together to deliver real‑time, multi‑LLM automation at scale.

## Why I Started This Project

* While there are already many tools that allow building agent workflows through diagrams, they surprisingly suffer from a lack of intuitiveness. For example, since agents correspond to LLMs, context, overall memory, and sandboxing are crucial - but these aspects are difficult to grasp at once with block diagrams. Moreover, even distinguishing between loops, conditionals, and agent tasks versus context wasn't intuitive even for me as a developer. I believed this issue is what makes it difficult for developers to easily move away from text-based programming.

## The Core of This Project

* First, to intuitively represent context, I expressed LLM instances as 'persons'. People don't forget their memories even when performing tasks. Therefore, even when Person A performs Task 1 and then Person B performs Task 2, Person A should retain that memory when performing Task 3. To actively manage such situations, persons exist as completely separate blocks as LLM instances, and workflows can be configured by assigning persons to each task.
* When two people have a conversation, there may be situations where one person periodically forgets the conversation while the other person needs to remember everything. To manage this, I placed memory in a 3-dimensional underground space. In other words, all overall LLM conversations are stored, but when a specific person needs to forget memories, those conversations are disconnected and become inaccessible only to that person.
* This underground space serves as a kind of sandboxing unit, i.e., an organizational unit. Here, the diagram's endpoints become the endpoints of the agent system, and when building A2A systems, you can construct A2A by simply connecting two diagrams. Additionally, each diagram is specified as a memory unit.
* Beyond just creating diagrams, I made it possible to receive the inputs and outputs of each diagram via API, allowing agent-based tools like Claude Code to utilize the diagrams. I also aimed to attempt visual collaboration where Claude Code could create diagrams on behalf of users or modify human-created diagrams.

## 프로젝트를 시작하게 된 계기:
* 이미 다이어그램을 통해 에이전트 워크플로우를 구축할 수 있는 툴은 많지만, 의외로 직관적이지 않다는 문제가 있습니다. 예를 들어 에이전트는 LLM에 해당하므로 context나 전반적인 메모리, 그리고 샌드박싱이 중요한데, 블록 다이어그램으로는 이런 내용들을 한번에 파악하기 어렵다는 문제가 있습니다. 더욱이 반복문, 조건문이나 에이전트의 작업과 context를 구분하는 것마저 개발자인 저한테도 직관적으로 와닿지 않았습니다. 이 문제가 개발자들이 텍스트 기반 프로그래밍에서 쉽게 벗어나기 어렵게 하는 부분이라 생각했습니다.

## 본 프로젝트의 핵심
우선 context를 직관적으로 표현하기 위해 LLM instance를 'person'으로 표현했습니다. 사람은 작업을 수행하더라도 기억을 잊지 않습니다. 따라서 사람 A가 작업 1을 한 다음 사람 B가 작업 2를 하더라도, 사람 A가 작업 3을 하는 상황에서는 그 기억을 보존해야 합니다. 이런 상황을 능동적으로 관리하기 위해 사람은 LLM instance로서 아예 다른 블록으로 존재하고, 각 작업에 사람을 할당하는 식으로 워크플로우를 구성할 수 있습니다.

* 두 사람이 대화를 할 때 한 사람은 주기적으로 대화를 잊어버리지만 다른 사람은 대화 내용을 전부 기억해야 하는 상황이 있을 수 있습니다. 이를 관리하기 위해 메모리를 3차원상의 지하 공간에 배치했습니다. 즉 전반적인 LLM의 대화는 모두 저장되지만, 특정 사람이 기억을 잊어야 하는 경우 해당 대화는 그 사람에게만 끊어져서 접근할 수 없는 방식입니다.

* 해당 지하 공간을 일종의 샌드박싱 단위, 즉 organization의 단위로 삼습니다. 여기서 다이어그램의 엔드포인트는 에이전트 시스템의 엔드포인트가 되며, A2A 시스템을 구축할 때 단순히 다이어그램 둘을 연결하는 것으로 A2A를 구축할 수 있습니다. 또한, 메모리 단위로 각 다이어그램으로 명시됩니다.

* 단순히 다이어그램을 만드는것만이 아니라 각 다이어그램의 입출력을 api로 받을 수 있게 하여 Claude Code와 같은 에이전트 기반 툴이 다이어그램을 활용할 수 있게 했습니다. Claude Code가 다이어그램을 대신 만들거나, 또 사람이 만든 다이어그램을 수정하는, 시각적인 협업도 시도하고자 했습니다.

## ✨ Key Capabilities

| Category                   | Highlights                                                                                    |
| -------------------------- | --------------------------------------------------------------------------------------------- |
| **Visual Workflow Design** | Drag‑and‑drop node editor with auto‑generated handles and right‑click context menus.          |
| **Multi‑LLM Execution**    | First‑class adapters for OpenAI, Anthropic, Google Gemini, Grok, and pluggable providers.     |
| **Streaming Runtime**      | Server‑sent events (SSE) stream node start/complete, cost, and memory updates live to the UI. |
| **Persistent Memory**      | Person‑scoped conversational memory with 3‑D “layer” visualisation.                           |
| **Cost & Usage Tracking**  | Fine‑grained token and dollar accounting per node and per run.                                |
| **Modular Packages**       | Reusable UI kit, diagram components, property panels, and typed data models.                  |
| **Secure File Ops**        | Sand‑boxed file I/O, path validation, size limits, and MIME checks.                           |

---

## 📂 Repository Layout

```
.
├── apps/
│   ├── web/        # React 19 + Vite frontend (AgentDiagram UI)
│   └── server/     # FastAPI backend (diagram executor)
│
├── packages/       # Shared, framework‑agnostic libraries
│   ├── core-model/     # TS types for nodes, arrows, persons, API keys
│   ├── ui-kit/         # Design‑system components (Button, Input, Select …)
│   ├── diagram-ui/     # React Flow node & edge primitives
│   ├── properties-ui/  # Dynamic property‑panel builder
│   └── hooks/          # Reusable React hooks (context menu, shortcuts …)
│
└── README.md       # ← you are here
```

---

## 🚀 Quick Start (Local Dev)

```bash
# 1. Clone
$ git clone https://github.com/your-org/agent-diagram.git
$ cd agent-diagram

# 2. Install deps (pnpm & Python virtualenv recommended)
$ pnpm install          # JS/TS workspace deps
$ cd apps/server && python -m venv venv && source venv/bin/activate
$ pip install -r requirements.txt

# 3. Environment
$ cp apps/server/.env.example apps/server/.env  # add your API keys

# 4. Run all services
# in one terminal
$ pnpm dev:web            # React dev server on :3000
# in another
$ uvicorn apps.server.main:app --reload --port 8000

# 5. Open http://localhost:3000 and start building diagrams!
```

---

## 🏗️ Core Packages at a Glance

| Package               | Purpose                                                                             |
| --------------------- | ----------------------------------------------------------------------------------- |
| `@repo/core-model`    | Central type definitions – DiagramState, Node/Arrow data, Person & API‑key schemas. |
| `@repo/ui-kit`        | Tailwind‑styled primitives: Button, Input, Select, Modal, Switch, Spinner …         |
| `@repo/diagram-ui`    | React Flow powered nodes, arrows, context menu, animations, handle helpers.         |
| `@repo/properties-ui` | Generic & field‑based property panels with auto‑save and loading states.            |
| `@repo/hooks`         | `useContextMenu`, `useKeyboardShortcuts`, `usePropertyForm`, and more.              |

> **Tip:** packages are completely framework‑agnostic except where React is unavoidable for UI rendering.

---

## 🌐 Frontend (`apps/web`)

* React 19 with concurrent features and Suspense.
* Tailwind CSS utility‑first styling, headless UI patterns.
* Zustand stores split into **diagram**, **UI**, **execution**, and **history** domains.
* React Flow canvas with smart snapping, bezier edges, and dynamic handle configs.
* Integrated dashboard for **conversation** and **properties** tabs.
* 3‑D memory layer tilt for conversation context exploration.

### Common NPM Scripts

```bash
pnpm dev:web           # Start Vite dev server
pnpm build:web         # Production build → dist/
pnpm analyze           # Bundle visualiser
```

---

## ⚙️ Backend (`apps/server`)

* FastAPI 0.111 with async/await throughout.
* Graph scheduler with topological sort, conditional branches, and loop detection.
* SSE streaming wrapper emitting `node_start`, `node_complete`, `execution_complete`, and heartbeats.
* Pluggable LLM adapters (`llm_service`) and person‑oriented memory service.
* Secure file service for uploads/downloads with size & MIME guards.
* Coverage‑enforced pytest suite, Locust load‑tests, and pre‑commit hooks.

### CLI Utilities

```bash
uvicorn main:app --reload --port 8000   # Dev server
pytest --cov=src                       # Run tests with coverage
locust -f tests/performance/locustfile.py   # Load testing
```

---

## 🧑‍💻 Contributing

1. **Fork & Branch** - `feature/<short-name>`.
2. **Commit** – Conventional Commits (`feat:`, `fix:`, `docs:` …).
3. **Test & Lint** – All packages and apps must pass `pnpm typecheck`, `pytest`, and ESLint.
4. **PR** – Describe motivation, usage, screenshots/GIFs where helpful.
5. **Review** – Address CI feedback, maintain ≥80% coverage.

We love issues and ideas! Feel free to open a discussion if you’re unsure where to start.

---

## 📜 License

This project is open‑source under the **MIT License**. See `LICENSE` for details.

---

## 🙏 Acknowledgements

* [React Flow](https://reactflow.dev/)
* [FastAPI](https://fastapi.tiangolo.com/)
* The amazing OSS community making agent tooling possible.
