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

## 핵심 개념
* 우선 context를 직관적으로 표현하기 위해 LLM instance를 'person'으로 표현했습니다. 사람은 작업을 수행하더라도 기억을 잊지 않습니다. 따라서 사람 A가 작업 1을 한 다음 사람 B가 작업 2를 하더라도, 사람 A가 작업 3을 하는 상황에서는 그 기억을 보존해야 합니다. 이런 상황을 능동적으로 관리하기 위해 사람은 LLM instance로서 아예 다른 블록으로 존재하고, 각 작업에 사람을 할당하는 식으로 워크플로우를 구성할 수 있습니다.

* 두 사람이 대화를 할 때 한 사람은 주기적으로 대화를 잊어버리지만 다른 사람은 대화 내용을 전부 기억해야 하는 상황이 있을 수 있습니다. 이를 관리하기 위해 메모리를 3차원상의 지하 공간에 배치했습니다. 즉 전반적인 LLM의 대화는 모두 저장되지만, 특정 사람이 기억을 잊어야 하는 경우 해당 대화는 그 사람에게만 끊어져서 접근할 수 없는 방식입니다.

* 해당 지하 공간을 일종의 샌드박싱 단위, 즉 organization의 단위로 삼습니다. 여기서 다이어그램의 엔드포인트는 에이전트 시스템의 엔드포인트가 되며, A2A 시스템을 구축할 때 단순히 다이어그램 둘을 연결하는 것으로 A2A를 구축할 수 있습니다. 또한, 메모리 단위로 각 다이어그램으로 명시됩니다.

* 단순히 다이어그램을 만드는것만이 아니라 각 다이어그램의 입출력을 api로 받을 수 있게 하여 Claude Code와 같은 에이전트 기반 툴이 다이어그램을 활용할 수 있게 했습니다. Claude Code가 다이어그램을 대신 만들거나, 또 사람이 만든 다이어그램을 수정하는, 시각적인 협업도 시도하고자 했습니다.

### Frontend (React/TypeScript)
```bash
pnpm dev:web          # Start development server (http://localhost:3000)
pnpm build:web        # Build production bundle
pnpm lint             # Run ESLint
pnpm lint:fix         # Auto-fix linting issues
pnpm typecheck        # TypeScript type checking
pnpm analyze          # Bundle size analysis (uses scripts/analyze-bundle.js)
```

### Backend (FastAPI/Python with Hypercorn)
```bash
python -m apps.server.main                        # Start server (http://localhost:8000)
WORKERS=4 python -m apps.server.main              # Start with 4 worker processes  
WORKERS=1 python -m apps.server.main              # Single worker for debugging

# Note: Hypercorn doesn't support hot reload. For development, restart server manually after changes.
```

### Testing
```bash
# Backend tests - NOTE: run_tests.py not found, verify testing approach with team
pytest apps/server/tests/                         # Run backend tests (if using pytest)
```

### CLI Tool
```bash
# Install CLI dependencies
pip install -r requirements-cli.txt

# Execution modes (now using WebSocket)
python tool.py run files/diagrams/example.json --mode=monitor   # Pre-load models, open browser, then run (recommended)
python tool.py run files/diagrams/example.json                  # Standard execution with browser
python tool.py run files/diagrams/example.json --mode=headless  # Backend-only execution
python tool.py run files/diagrams/example.json --mode=check     # Run and analyze conversation logs
python tool.py run files/diagrams/example.json --debug          # Debug mode with verbose output

# LLM YAML support
python tool.py run diagrams/workflow.llm-yaml             # Execute LLM-friendly YAML format
python tool.py convert workflow.llm-yaml example.json      # Convert between formats
```

## Architecture Overview

DiPeO (Diagrammed People & Organizations) is a visual programming environment for AI agent workflows with a **unified backend execution model**. All diagram execution now happens through WebSocket connections, enabling real-time control and monitoring.

### Core Concepts
- **Person-based LLM Instances**: LLMs as "persons" with persistent memory
- **Visual Programming**: Drag-and-drop workflow creation
- **Memory Layer**: 3D underground visualization of conversation history
- **Organization Units**: Diagrams as sandboxed execution environments

### Execution Flow
```
Frontend (React) ←→ Backend (FastAPI)
        ↓               ↓
   WebSocket      WebSocket Handler
   Connection           ↓
        ↓        Unified Execution Engine
   Bidirectional        ↓
   Control Flow    Executor Factory
                        ↓
              Node Type Executors
```

## Node Types (All Backend-Executed)

| Node Type | Purpose | Key Features |
|-----------|---------|--------------|
| `start` | Flow initialization | Static data output |
| `condition` | Branching logic | Boolean paths, detect_max_iterations |
| `job` | Code execution | Python/JS/Bash sandboxes |
| `endpoint` | Terminal operations | File saving, outputs |
| `person_job` | LLM API calls | Memory, iterations, prompts |
| `person_batch_job` | Batch LLM ops | Multiple input processing |
| `db` | Data operations | File I/O, database access |
| `user_response` | User input | Interactive prompts with timeout |
| `notion` | Notion integration | Read/write Notion pages |

**Note**: All node types use snake_case everywhere (no conversion needed).

## Loop Implementation

PersonJob nodes support iteration with Condition nodes:

1. **PersonJob Configuration**:
   - `maxIterations`: Max executions per node
   - `firstOnlyPrompt`: First iteration only (count=0)
   - `defaultPrompt`: Subsequent iterations (count>0)

2. **Condition Node** (`conditionType: "detect_max_iterations"`):
   - Returns `false` while any node hasn't reached limit
   - Returns `true` when all nodes reached limits
   - Arrow from here holds 'generic' content type which feeds what it got.

## Execution Control Features

With WebSocket-based execution, you can control running diagrams in real-time:

### Node-Level Control (Fully Implemented)
- **Pause**: Temporarily halt a node's execution - node waits until resumed
- **Resume**: Continue a paused node - execution proceeds from where it paused
- **Skip**: Bypass a node entirely - marks as skipped and continues flow

### Execution-Level Control
- **Abort**: Stop entire execution immediately
- **Monitor**: Watch any execution in progress

### Interactive Prompts
- Nodes can request user input during execution
- `user_response` node: Dedicated node for user interaction
  - Customizable prompt message with {{variable}} substitution
  - Configurable timeout (1-60 seconds, default 10)
  - Shows popup modal in browser
  - Returns response or null on timeout
- PersonJob nodes also support interactive prompts
- Automatic continuation on timeout

Example user_response configuration:
```json
{
  "type": "user_response",
  "promptMessage": "Please provide {{input_type}} for {{task_name}}",
  "timeoutSeconds": 30
}
```

## LLM YAML Format

Simplified format for AI agent collaboration:

```yaml
flow:
  - start -> analyze: "data"
  - analyze -> report: "results"

prompts:
  analyze: "Analyze: {{data}}"
  report: "Report on: {{results}}"

agents:
  analyst:
    model: "gpt-4.1-nano"
    service: "openai"
```

**Features**:
- Natural flow syntax with `->` arrows
- Variable passing with `: "variable_name"`
- Automatic node type inference
- `{{variable}}` substitution

## API Endpoints

### WebSocket (All Execution)
- `WS /api/ws` - **All diagram execution now happens here**
  - Bidirectional communication with auto-reconnection
  - Handles execution, control, monitoring, and interactive features

#### WebSocket Message Types
- **Execution**: `{ type: 'execute_diagram', diagram: {...}, options: {...} }`
- **Control**: 
  - `{ type: 'pause_node', nodeId: '...' }`
  - `{ type: 'resume_node', nodeId: '...' }`
  - `{ type: 'skip_node', nodeId: '...' }`
  - `{ type: 'abort_execution', executionId: '...' }`
- **Interactive**: `{ type: 'interactive_response', nodeId: '...', response: '...' }`
- **Monitoring**: `{ type: 'subscribe_monitor', executionId: '...' }`
- **Heartbeat**: `{ type: 'heartbeat' }`

### REST Endpoints (Utilities Only)
- `GET /api/diagrams/execution-capabilities` - Supported node types and features
- `POST /api/diagrams/save` - Save diagrams to files
- `POST /api/diagrams/convert` - Convert between formats (JSON/YAML/LLM-YAML)
- `GET /api/diagrams/health` - Health check

### WebSocket Event Types
```javascript
// Execution lifecycle
{type: 'execution_started', execution_id: '...', total_nodes: 5}
{type: 'node_start', nodeId: '...', nodeType: 'person_job'}
{type: 'node_progress', nodeId: '...', message: 'Processing...'}
{type: 'node_complete', nodeId: '...', output: {...}, total_token_count: 0.02}
{type: 'node_skipped', nodeId: '...', reason: 'max_iterations_reached'}
{type: 'node_error', nodeId: '...', error: 'Connection timeout'}
{type: 'execution_complete', total_token_count: 0.05, duration: 3.2}

// Control events
{type: 'node_paused', nodeId: '...'}
{type: 'node_resumed', nodeId: '...'}
{type: 'node_skip_requested', nodeId: '...'}
{type: 'execution_abort_requested', executionId: '...'}
{type: 'execution_aborted', executionId: '...'}

// Interactive events
{type: 'interactive_prompt', nodeId: '...', prompt: '...', timeout: 30}
{type: 'interactive_response_received', nodeId: '...'}
{type: 'interactive_prompt_timeout', nodeId: '...'}
```

## Key File Locations

### Backend
- `apps/server/src/engine/` - Execution engine
  - `engine.py` - Main orchestrator
  - `executors/` - Node executors (one per node type)
- `apps/server/src/api/routers/websocket.py` - **All execution happens here**
- `apps/server/src/api/routers/diagram.py` - Utility endpoints only (save/convert/health)
- `apps/server/src/llm/adapters/` - LLM provider adapters
- `apps/server/src/services/` - Business logic services

### Frontend
- `apps/web/src/utils/websocket/execution-client.ts` - WebSocket execution client
- `apps/web/src/utils/websocket/client.ts` - WebSocket connection wrapper
- `apps/web/src/hooks/useDiagramRunner.ts` - Execution hook
- `apps/web/src/stores/` - Zustand stores for state management
  - `executionStore.ts` - Execution state tracking
  - `diagramStore.ts` - Diagram state management
  - `consolidatedUIStore.ts` - UI state consolidation
- `apps/web/src/types/` - TypeScript type definitions
- `apps/web/src/config/` - Node configuration files (separate per node type)
- `apps/web/src/components/canvas/` - Visual diagram components

### Tools
- `tool.py` - CLI for diagram execution
- `files/diagrams/` - Diagram storage (.json, .yaml, .llm-yaml)

## Development Guidelines

- **Monorepo Structure**: Project uses pnpm workspaces with apps/web and apps/server
- **Package Manager**: Use `pnpm` exclusively (no npm/npx/node)
- **Default Model**: `gpt-4.1-nano` for OpenAI
- **Type Safety**: Run `pnpm typecheck` before commits
- **Diagram Storage**: Save to `/files/diagrams/`
- **API Keys**: Use `APIKEY_TEST00` for testing
- **Python Module Execution**: Use `python -m` for running modules
- **Node Configuration**: Each node type has its own config file in `apps/web/src/config/`

## Adding New Features

### New Node Type
1. Add to `NodeType` enum in `apps/server/src/constants.py`
2. Create executor in `apps/server/src/engine/executors/`
3. Implement `validate()` and `execute()` methods
4. Register in `ExecutorFactory`
5. Add configuration file in `apps/web/src/config/`
6. Add WebSocket event handlers if node requires interactive control

### New LLM Provider
1. Create adapter in `apps/server/src/llm/adapters/`
2. Implement `chat()` method
3. Register in `apps/server/src/llm/factory.py`

### New WebSocket Control Feature
1. Add message type to WebSocket handler in `apps/server/src/api/routers/websocket.py`
2. Implement control logic in execution engine
3. Add client-side message handling in `websocket-execution-client.ts`
4. Update UI controls as needed

## Browser State Persistence

- Nodes/arrows auto-save to localStorage
- Person definitions persist
- API keys NOT persisted (security)
- State restored on page load