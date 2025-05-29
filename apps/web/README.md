# AgentDiagram Frontend – Essential Guide

## 1. Overview

AgentDiagram Frontend is a React‑19 + TypeScript application that lets you design, execute, and monitor multi‑LLM agent workflows through an intuitive drag‑and‑drop diagram editor.

Key capabilities:

* Visual workflow authoring with React Flow nodes/edges
* Out‑of‑the‑box connectors for OpenAI, Anthropic, Gemini, Grok
* Live execution streaming and token/cost tracking
* 3D memory‑layer visualisation

## 2. Core Tech Stack

* **React 19** (concurrent features)
* **TypeScript**
* **Zustand** for state management
* **React Flow** for diagrams
* **Tailwind CSS** for styling
* **Vite** build tool

## 3. Project Skeleton (condensed)

```text
apps/web
  └─ src
     ├─ components/        UI + nodes
     ├─ stores/            Zustand state
     ├─ hooks/             Custom hooks
     ├─ utils/             Helpers & export
```

## 4. Main UI Components

* **TopBar** – file operations, run controls, API keys
* **Sidebar** – node palette, personas, import
* **DiagramCanvas** – React Flow canvas
* **Dashboard** – conversation & properties tabs

### Node Types (selected)

| Node              | Purpose               |
| ----------------- | --------------------- |
| **StartNode**     | Entry point           |
| **PersonJobNode** | LLM call with persona |
| **ConditionNode** | True / false branch   |
| **DBNode**        | Data source           |
| **JobNode**       | Code / API execution  |
| **EndpointNode**  | Terminate / save      |

## 5. State Stores (keys only)

* **consolidatedDiagramStore** – nodes, arrows, persons, apiKeys
* **consolidatedUIStore** – selected\*, dashboardTab, isMemoryLayerTilted
* **executionStore** – runContext, runningNodes, currentRunningNode

## 6. Developer Guide

```bash
pnpm install       # dependencies
pnpm dev:web       # dev server @localhost:3000
pnpm build:web     # production build
pnpm analyze       # bundle stats
```

## 7. Testing Strategy

1. **Component** – render & interaction
2. **Integration** – execution flow, SSE
3. **E2E** – full workflow create → run → export

## 8. Performance & Optimisation

* Code‑split heavy panels
* Memoise node components; debounced property updates
* Virtualise long lists; optimise SVG edge rendering

## 9. Security Essentials

* Backend‑stored encrypted API keys
* Sandboxed backend code execution
* Size/MIME validation on uploads
* Rate limiting & input validation

## 10. Troubleshooting Cheatsheet

| Symptom               | Quick Checks                                  |
| --------------------- | --------------------------------------------- |
| Nodes not updating    | call `useUpdateNodeInternals` after mutations |
| Streaming blank       | backend on :8000? SSE errors?                 |
| Handles won’t connect | handle IDs & configs                          |
| Slow large diagrams   | profiler, avoid unnecessary re‑renders        |

## 11. API Endpoints (dev proxy)

* `POST /api/run-diagram`
* `GET/POST /api/apikeys`
* `GET /api/conversations`
* `POST /api/save`

## 12. Further Reading

* React Flow documentation
* Zustand usage guide
* Tailwind CSS docs
* Vite configuration reference
