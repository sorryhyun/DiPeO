# DiPeO, Diagrammed People (agents) & Organizations (agent system)
![image info](/img.png)

DiPeO(daɪpiːɔː) is a **monorepo** for building, executing, and monitoring AI‑powered agent workflows through an intuitive visual programming environment. The repository is composed of reusable TypeScript **packages**, a React‑based **frontend**, and a FastAPI **backend** that work together to deliver real‑time, multi‑LLM automation at scale.

## 핵심 기능

1. LLM과 작업 블록의 분리를 통한 직관적인 컨텍스트 관리
2. diagram의 yaml 형태 표현 및 실행 tool 제공
3. 다이어그램 엔드포인트를 활용한 A2A canvas 제공

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
uvicorn apps.server.main:app --reload --port 8000
```

## Why I Started This Project

* While there are already many tools that allow building agent workflows through diagrams, they surprisingly suffer from a lack of intuitiveness. For example, since agents correspond to LLMs, context, overall memory, and sandboxing are crucial - but these aspects are difficult to grasp at once with block diagrams. Moreover, even distinguishing between loops, conditionals, and agent tasks versus context wasn't intuitive even for me as a developer. I believed this issue is what makes it difficult for developers to easily move away from text-based programming.

First, to intuitively represent context, the LLM instance is depicted as a “person.” A person does not forget memories even when performing tasks. Therefore, if person A completes task 1 and then person B completes task 2, when person A goes on to perform task 3, that memory must be preserved. To actively manage such situations, each person exists as a separate block as an LLM instance, and the workflow can be organized by assigning a person to each task.

When two people are having a conversation, there may be a situation where one person periodically forgets the conversation, but the other person must remember the entire conversation. To manage this, memories are placed in a three-dimensional underground space. In other words, all of the LLM’s conversation history is stored, but if a particular person needs to forget certain parts, those conversations are severed only for that person so they cannot access them.

This diagram system is the same as a standard diagram flow system, but it includes several mechanisms for managing loops and conditions:

If an arrow is connected to the “first_only” handle of a person-job block, that block will initially ignore any data coming in through its default handle. Only when it runs again will it accept data from the default handle.

The “max iteration” of a person-job block indicates the maximum number of times that block can execute. After reaching that number of executions, it will ignore further requests.

A condition block has two options: “detect max iteration” and “expression.” In the case of “detect max iteration,” it triggers when, within a cycle, all person-job blocks have reached their max iterations.

The canvas space serves as a kind of sandbox unit, effectively an organizational unit. Here, the endpoint of a diagram becomes the endpoint of an agent system. When building an A2A (agent-to-agent) system, you can simply connect two diagrams to establish A2A. In addition, memory units are explicitly designated per diagram.

Rather than merely creating diagrams, the inputs and outputs of each diagram can be exposed via API, enabling agent-based tools like Claude Code to leverage the diagrams. We aim to explore visual collaboration in which Claude Code can generate diagrams on its own or a human can modify a diagram created by Claude Code.
## 프로젝트를 시작하게 된 계기:
* 이미 다이어그램을 통해 에이전트 워크플로우를 구축할 수 있는 툴은 많지만, 의외로 직관적이지 않다는 문제가 있습니다. 예를 들어 에이전트는 LLM에 해당하므로 context나 전반적인 메모리, 그리고 샌드박싱이 중요한데, 블록 다이어그램으로는 이런 내용들을 한번에 파악하기 어렵다는 문제가 있습니다. 더욱이 반복문, 조건문이나 에이전트의 작업과 context를 구분하는 것마저 개발자인 저한테도 직관적으로 와닿지 않았습니다. 이 문제가 개발자들이 텍스트 기반 프로그래밍에서 쉽게 벗어나기 어렵게 하는 부분이라 생각했습니다.

## 본 프로젝트의 핵심
우선 context를 직관적으로 표현하기 위해 LLM instance를 'person'으로 표현했습니다. 사람은 작업을 수행하더라도 기억을 잊지 않습니다. 따라서 사람 A가 작업 1을 한 다음 사람 B가 작업 2를 하더라도, 사람 A가 작업 3을 하는 상황에서는 그 기억을 보존해야 합니다. 이런 상황을 능동적으로 관리하기 위해 사람은 LLM instance로서 아예 다른 블록으로 존재하고, 각 작업에 사람을 할당하는 식으로 워크플로우를 구성할 수 있습니다.

* 두 사람이 대화를 할 때 한 사람은 주기적으로 대화를 잊어버리지만 다른 사람은 대화 내용을 전부 기억해야 하는 상황이 있을 수 있습니다. 이를 관리하기 위해 메모리를 3차원상의 지하 공간에 배치했습니다. 즉 전반적인 LLM의 대화는 모두 저장되지만, 특정 사람이 기억을 잊어야 하는 경우 해당 대화는 그 사람에게만 끊어져서 접근할 수 없는 방식입니다.

* 해당 지하 공간을 일종의 샌드박싱 단위, 즉 organization의 단위로 삼습니다. 여기서 다이어그램의 엔드포인트는 에이전트 시스템의 엔드포인트가 되며, A2A 시스템을 구축할 때 단순히 다이어그램 둘을 연결하는 것으로 A2A를 구축할 수 있습니다. 또한, 메모리 단위로 각 다이어그램으로 명시됩니다.

* 단순히 다이어그램을 만드는것만이 아니라 각 다이어그램의 입출력을 api로 받을 수 있게 하여 Claude Code와 같은 에이전트 기반 툴이 다이어그램을 활용할 수 있게 했습니다. Claude Code가 다이어그램을 대신 만들거나, 또 사람이 만든 다이어그램을 수정하는, 시각적인 협업도 시도하고자 했습니다.

## Overview

DiPeO implements a **unified backend execution model** that consolidates all diagram execution logic on the server side, providing consistent behavior across browser, CLI, and API access.

## Architecture

```
Frontend (React) ←→ Backend (FastAPI/Python)
       ↓                     ↓
   API Client     Unified Execution Engine
                         ↓
                   Executor Factory
                         ↓
    All Node Types: Start, Condition, Job, Endpoint,
                   PersonJob, PersonBatchJob, DB
```

### Execution Architecture

- **Unified Execution Engine**: All nodes execute on the backend
- **SSE Streaming**: Real-time execution updates via Server-Sent Events
- **Executor Factory**: Creates appropriate executors for each node type
- **Unified Node Types**: All components use snake_case format (`start`, `person_job`, etc.)

## Node Types (All Backend-Executed)

| Node Type | Purpose | Key Features |
|-----------|---------|--------------|
| **Start** | Initializes execution flow | Static data output |
| **Condition** | Boolean logic and branching | True/false paths, detect_max_iterations |
| **Job** | Sandboxed code execution | Python/JS/Bash support |
| **Endpoint** | Terminal nodes | File saving, final outputs |
| **PersonJob** | LLM API calls | Memory, max_iterations, firstOnlyPrompt |
| **PersonBatchJob** | Batch LLM operations | Processes multiple inputs |
| **DB** | Data operations | File I/O, database access |

## LLM YAML Format

DiPeO supports a simplified, LLM-friendly YAML format for easy diagram creation:

```yaml
flow:
  - start -> analyze: "data"
  - analyze -> report: "results"
  - report -> end

prompts:
  analyze: "Analyze this data: {{data}}"
  report: "Create a report based on: {{results}}"

agents:
  analyst:
    model: "gpt-4.1-nano"
    service: "openai"
```

## Execution Flow

```python
# 1. Unified execution endpoint receives diagram
POST /api/run-diagram

# 2. Server-side execution with SSE streaming
- Dependency resolution and planning
- Sequential/parallel node execution
- Real-time progress updates
- Memory and context management

# 3. Client receives streaming updates
{type: 'node_start', nodeId: '...'}
{type: 'node_complete', nodeId: '...', output: {...}}
{type: 'execution_complete', total_cost: 0.05}
```

## Loop Implementation

Loops use PersonJob nodes with `iterationCount` and Condition nodes:

1. **PersonJob Node Configuration**:
   - `iterationCount`: Maximum execution count per node
   - `firstOnlyPrompt`: Used only on first execution (count=0)
   - `defaultPrompt`: Used for subsequent iterations (count>0)
   - Node skips when execution count >= iterationCount

2. **Condition Node** (`conditionType: "detect_max_iterations"`):
   - Returns `false` while ANY node with iterationCount hasn't reached its limit
   - Returns `true` when ALL nodes with iterationCount have reached their limits
   - Acts as the loop exit gate

**Example Flow**: Two PersonJob nodes (iterationCount=2) → Condition node
- Iteration 1: Both execute (count 0→1), Condition returns `false`
- Iteration 2: Both execute (count 1→2), Condition returns `false`
- Iteration 3: Both skip (count=2), Condition returns `true` → loop exits

## Key Features

### Variable Substitution
- **Arrow Labels**: Become variable names (e.g., arrow "topic" → `{{topic}}`)
- **Frontend**: `getInputValues()` maps arrow labels to variables
- **Backend**: `_substitute_variables()` replaces `{{var}}` patterns

### Dependency Management
- Topological sorting for optimal execution order
- Cycle detection with loop controller
- First-only handle logic for PersonJob nodes
- Condition branching with true/false paths

### Execution Context
- **nodeOutputs**: Results from each node execution
- **nodeExecutionCounts**: Iteration tracking for loops
- **conditionValues**: Branch decisions for conditional flow
- **executionOrder**: Sequential record of execution
- **totalCost**: Aggregated LLM API costs

### Advanced Controls
- **Loop Management**: Max iteration enforcement per node
- **Skip Management**: Centralized skip logic with reasons
- **Streaming Updates**: Real-time execution via SSE
- **Error Handling**: Continue-on-error in debug mode

## Backend API Endpoints

### V2 Unified Execution
- `POST /api/run-diagram` - Main execution endpoint with SSE streaming
  - Request body: `{ "diagram": {...}, "options": {...} }`
  - Returns SSE stream with real-time execution updates
- `GET /api/execution-capabilities` - Feature discovery

## CLI Tool Integration

The Python CLI tool directly interacts with the backend API:

```bash
# Unified run command with execution modes
python tool.py run diagrams/example.json --mode=monitor   # Pre-load models, open browser, then run
python tool.py run diagrams/example.json                  # Standard execution with browser
python tool.py run diagrams/example.json --mode=headless  # Pure backend execution (no browser)
python tool.py run diagrams/example.json --mode=check     # Run and analyze conversation logs

# LLM YAML execution - supports simplified YAML format
python tool.py run diagrams/workflow.llm-yaml --mode=monitor  # Execute LLM YAML with browser
python tool.py run diagrams/workflow.yaml                     # Auto-detects format
```

**Execution Modes:**
- `monitor`: Pre-loads LLM models, opens browser visualization, then executes
- `headless`: Pure backend execution without browser
- `check`: Executes and analyzes conversation logs
- Default: Standard execution with browser visualization

## Benefits

- **Unified Architecture**: Consistent execution behavior across all environments
- **Real-time Monitoring**: SSE streaming provides live execution updates
- **LLM YAML Support**: AI-friendly format for diagram creation and collaboration
- **Type Safety**: Unified snake_case node types throughout the system
- **Memory Management**: Person-based instances with persistent memory

## File Locations

### Backend
- `apps/server/src/engine/` - Unified execution engine
  - `engine.py` - Main orchestrator
  - `executors/` - Node executor implementations
  - `planner.py` - Execution planning
  - `resolver.py` - Dependency resolution
- `apps/server/src/api/routers/diagram.py` - V2 API endpoints
- `apps/server/src/services/` - Business logic services
- `apps/server/src/llm/` - LLM provider adapters

### Frontend
- `apps/web/src/engine/unified-execution-client.ts` - V2 API client
- `apps/web/src/features/execution/hooks/useDiagramRunner.ts` - React execution hook
- `apps/web/src/global/` - Global state management
- `apps/web/src/shared/types/` - TypeScript type definitions

### CLI & Tools
- `tool.py` - Python CLI for diagram execution
- `scripts/convert-diagram.ts` - LLM YAML converter
- `files/diagrams/` - Diagram storage directory

## Development

### Common Commands

#### Frontend (React/TypeScript)
```bash
pnpm dev:web          # Start development server (http://localhost:3000)
pnpm build:web        # Build production bundle
pnpm lint             # Run ESLint
pnpm lint:fix         # Auto-fix linting issues
pnpm typecheck        # TypeScript type checking
pnpm analyze          # Bundle size analysis
```

#### Backend (FastAPI/Python)
```bash
python apps.server.main.py                        # Start server (http://localhost:8000)
RELOAD=true python apps.server.main.py            # Start with auto-reload for development
```

### Development Guidelines

- **Package Manager**: Use `pnpm` only (no npm/npx/node)
- **LLM Model**: Default to `gpt-4.1-nano` for OpenAI
- **Diagram Storage**: Save to `files/diagrams/` directory
- **Type Safety**: Run `pnpm typecheck` before commits
- **Testing**: Run appropriate test suites before merging
- **Documentation**: Update CLAUDE.md files after architectural changes