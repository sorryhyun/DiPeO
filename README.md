# DiPeO, Diagrammed People (agents) & Organizations (agent system)
![image info](/img.png)

DiPeO(daɪpiːɔː) is a **monorepo** for building, executing, and monitoring AI‑powered agent workflows through an intuitive visual programming environment. The repository is composed of reusable TypeScript **packages**, a React‑based **frontend**, and a FastAPI **backend** that work together to deliver real‑time, multi‑LLM automation at scale.

## 핵심 기능

1. LLM과 작업 블록의 분리를 통한 직관적인 컨텍스트 관리
2. diagram의 yaml 형태 표현 및 실행 tool 제공
3. 다이어그램 엔드포인트를 활용한 A2A canvas 제공 (구현 예정)

## Why I Started This Project

* While there are already many tools that allow building agent workflows through diagrams, they surprisingly suffer from a lack of intuitiveness. For example, since agents correspond to LLMs, context, overall memory, and sandboxing are crucial - but these aspects are difficult to grasp at once with block diagrams. Moreover, even distinguishing between loops, conditionals, and agent tasks versus context wasn't intuitive even for me as a developer. I believed this issue is what makes it difficult for developers to easily move away from text-based programming.

## 프로젝트를 시작하게 된 계기:
* 이미 다이어그램을 통해 에이전트 워크플로우를 구축할 수 있는 툴은 많지만, 의외로 직관적이지 않다는 문제가 있습니다. 예를 들어 에이전트는 LLM에 해당하므로 context나 전반적인 메모리, 그리고 샌드박싱이 중요한데, 블록 다이어그램으로는 이런 내용들을 한번에 파악하기 어렵다는 문제가 있습니다. 더욱이 반복문, 조건문이나 에이전트의 작업과 context를 구분하는 것마저 개발자인 저한테도 직관적으로 와닿지 않았습니다. 이 문제가 개발자들이 텍스트 기반 프로그래밍에서 쉽게 벗어나기 어렵게 하는 부분이라 생각했습니다.

# Quickstart

```bash
git clone https://github.com/sorryhyun/DiPeO.git
pnpm install
pnpm dev:web

python -m venv apps/server/.venv
source apps/server/.venv/bin/activate
pip install -r apps/server/requirements.txt
bash run-server.sh
```

## Key Concepts

* First, to intuitively represent context, the LLM instance is depicted as a “person.” A person does not forget memories even when performing tasks. Therefore, if person A completes task 1 and then person B completes task 2, when person A goes on to perform task 3, that memory must be preserved. To actively manage such situations, each person exists as a separate block as an LLM instance, and the workflow can be organized by assigning a person to each task.

* When two people are having a conversation, there may be a situation where one person periodically forgets the conversation, but the other person must remember the entire conversation. To manage this, memories are placed in a three-dimensional underground space. In other words, all of the LLM’s conversation history is stored, but if a particular person needs to forget certain parts, those conversations are severed only for that person so they cannot access them.

* This diagram system is the same as a standard diagram flow system, but it includes several mechanisms for managing loops and conditions:

    * If an arrow is connected to the “first_only” handle of a person-job block, that block will initially ignore any data coming in through its default handle. Only when it runs again will it accept data from the default handle.

    * The “max iteration” of a person-job block indicates the maximum number of times that block can execute. After reaching that number of executions, it will ignore further requests.

    * A condition block has two options: “detect max iteration” and “expression.” In the case of “detect max iteration,” it triggers when, within a cycle, all person-job blocks have reached their max iterations.

* The canvas space serves as a kind of sandbox unit, effectively an organizational unit. Here, the endpoint of a diagram becomes the endpoint of an agent system. When building an A2A (agent-to-agent) system, you can simply connect two diagrams to establish A2A. In addition, memory units are explicitly designated per diagram.

* Rather than merely creating diagrams, the inputs and outputs of each diagram can be exposed via API, enabling agent-based tools like Claude Code to leverage the diagrams. We aim to explore visual collaboration in which Claude Code can generate diagrams on its own or a human can modify a diagram created by Claude Code.
# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working with DiPeO.

## Quick Start

```bash
# Frontend
pnpm dev:web        # Dev server (localhost:3000)
pnpm build:web      # Production build  
pnpm lint:fix       # Fix linting
pnpm typecheck      # Type checking

# Backend  
python -m apps.server.main  # Start server (localhost:8000)
WORKERS=4 python -m apps.server.main  # Multi-worker mode

# CLI Tool
pip install -r requirements-cli.txt
python tool.py run files/diagrams/diagram.json --mode=monitor
```

## Architecture

**DiPeO** - Visual programming for AI agent workflows via WebSocket with real-time control.

**Core**: Person-based LLMs with memory • Visual drag-drop workflows • 3D memory visualization

**Flow**: Frontend ↔ WebSocket ↔ Execution Engine → Node Executors

**UI Modes**: Design (canvas+properties) • Execution (conversation dashboard)

## Node Types

- **start**: Flow init with static data (output only)
- **condition**: Boolean branching, detect_max_iterations
- **job**: Code execution (Python/JS/Bash)
- **endpoint**: Terminal ops, file saving (input only)
- **person_job**: LLM calls with memory/iterations
- **person_batch_job**: Batch LLM processing
- **db**: Data operations, file I/O
- **user_response**: Interactive prompts (1-60s timeout)
- **notion**: Notion page read/write

All use snake_case naming.

## Handle System

Arrows connect handles (`nodeId:handleName`), not nodes directly.

- Format: `nodeId:handleName`
- Registry: `apps/web/src/config/handleRegistry.ts`
- Special: start (output only), endpoint (input only), condition (input + true/false)
- Standard positioning: input (left), output (right) to prevent overlap
- Optimized: Memoized FlowHandle, pre-computed lookups

## Export/Import

**Formats**: JSON (v3.0.0 with labels), YAML/LLM-YAML (array-based)

```typescript
// New (recommended)
import { useExport } from '@/hooks';
const { exportDiagram, importDiagram } = useExport();

// Legacy (deprecated)
import { exportDiagramState, loadDiagram } from '@/hooks/useStoreSelectors';
```

**File Naming**: Default filename is `diagram.json`. Backend auto-increments with `_1`, `_2` etc. if file exists.

**Unique Labels**: Duplicate labels get alphabetic suffixes: `-a`, `-b`, `-c` etc.

**Immer Fix**: Use store actions (addNode, addArrow, etc.) instead of direct Map mutations in import

## Memory & Loops

- **Memory**: 1000 msg limit, Redis (24h TTL) or in-memory
- **Logs**: Auto JSONL to `files/conversation_logs/`
- **PersonJob**: `maxIterations`, `firstOnlyPrompt` (count=0), `defaultPrompt` (count>0)
- **Condition**: `detect_max_iterations` - false until all nodes reach limit

## LLM YAML Format

```yaml
flow:
  - start -> analyze: "data"
  - analyze -> report: "results"
prompts:
  analyze: "Analyze: {{data}}"
persons:
  analyst:
    model: "gpt-4.1-nano"
    service: "openai"
```

## APIs

**WebSocket** (`WS /api/ws`): All execution control
- Messages: `execute_diagram`, `pause_node`, `resume_node`, `skip_node`, `abort_execution`
- Backend expects arrays for nodes/arrows (auto-converted from frontend Records)

**REST**: `/api/diagrams/*`, `/api/api-keys/`, `/api/conversations`, `/api/files/upload`

## Key Files

**Backend**:
- `apps/server/src/engine/` - Execution engine
- `apps/server/src/api/routers/websocket.py` - WebSocket handler
- `apps/server/src/llm/adapters/` - LLM providers

**Frontend**:
- `apps/web/src/hooks/` - Consolidated hooks
  - `useCanvasOperations` - Canvas interactions
  - `useExecution` - Execution controls
  - `useExport` - Import/export (NEW)
  - `useDiagramManager` - Diagram lifecycle
- `apps/web/src/stores/unifiedStore.ts` - Zustand store
- `apps/web/src/config/handleRegistry.ts` - Handle definitions

## Type System

- **Primitives** (`/types/primitives/`): Base types (geometry, enums, utilities)
- **Domain** (`/types/domain/`): Business logic (node, arrow, handle, person, diagram)
- **Framework** (`/types/framework/`): @xyflow/react adapters
- **UI** (`/types/ui/`): Interface state
- **Runtime** (`/types/runtime/`): Execution, WebSocket, events

## Usage Examples

```typescript
// Canvas operations
const canvas = useCanvasOperations();
canvas.addNode('person_job', { x: 100, y: 100 });
canvas.connectNodes(sourceId, 'default', targetId, 'first');

// Execution
const execution = useExecution();
execution.execute(diagram);
execution.pauseNode(nodeId);

// Store (with transactions)
const store = useUnifiedStore();
store.transaction(() => {
  store.addNode('job', { x: 200, y: 100 });
  store.addArrow(sourceHandle, targetHandle);
});
```

## WebSocket Event Bus

Single connection in App.tsx:
```typescript
// App.tsx only
const execution = useExecution({ autoConnect: true });

// Other components
const { send, on } = useWebSocketEventBus();
const unsub = on('node_complete', handler);
```

## Dev Guidelines

- Use `pnpm` only
- Python modules: `python -m`
- Frontend `data` ↔ Backend `properties`
- Zustand 5: Use `useShallow` for complex selectors
- Person naming: `DomainPerson` uses `label` field (not `name`)

## Performance

- Position updates on drag end only
- Tolerance validation (0.01)
- Memoized conversions by collection size
- Stable dependencies in ConversationDashboard

## Adding Features

- **New Node**: Add to NodeType enum → Create executor → Add config
- **New LLM**: Create adapter → Implement chat()
- **New Control**: Add WS message → Implement in engine → Update client