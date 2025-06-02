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

## Overview

DiPeO implements a **hybrid client-server execution model** that intelligently orchestrates diagram execution between frontend and backend environments based on security and capability requirements.

## Architecture Layers

```
Frontend (React/Node.js) ←→ Backend (FastAPI/Python)
    ↓                           ↓
Client-Safe Executors      Server-Only Executors
(Start, Condition, Job,    (PersonJob, DB blocks)
 Endpoint)
```

### Execution Orchestration

- **`ExecutionOrchestrator`**: Auto-detects environment, routes execution
- **`ExecutionEngine`**: Core execution logic with dependency resolution  
- **`ExecutorFactory`**: Creates environment-appropriate executors
- **Base Executors**: Abstract classes for client-safe vs server-only operations

## Node Classification

### Client-Safe Nodes (Local Execution)
- **Start**: Initializes execution flow with static data
- **Condition**: Boolean logic and branching  
- **Job**: Stateless operations and safe code execution
- **Endpoint**: Terminal nodes with optional file saving

### Server-Only Nodes (Backend API Calls)
- **PersonJob/PersonBatchJob**: LLM API calls with memory management
- **DB**: File I/O, database operations, data sources

## Execution Strategies

1. **Client-Only**: All nodes execute locally
2. **Server-Only**: All nodes require backend execution
3. **Hybrid**: Mixed execution with selective API calls

## Execution Flow Algorithm

```typescript
// 1. Dependency Analysis & Planning
const plan = dependencyResolver.createExecutionPlan(diagram);

// 2. Environment-Based Executor Selection  
const executors = executorFactory.createExecutors(plan.strategy);

// 3. Iterative Node Execution
while (pendingNodes.size > 0) {
  for (const node of readyNodes) {
    if (isClientSafe(node)) {
      result = executeLocally(node);
    } else {
      result = await callBackendAPI(node); // /api/nodes/{type}/execute
    }
    updateContext(result);
  }
}
```

## Loop Algorithm

- There is no special mechanism dedicated to loops, but a loop can be implemented using the following two mechanisms:

1. The person job block has an attribute called max_iteration. Once the block has been executed up to the number of times specified by max_iteration, it will be skipped for any subsequent requests. During this skipping, the forget rule does not apply, and all inputs are counted regardless of whether they were received via the first only handle or the default handle. For reference, the first only handle is used only for the initial execution of the block, after which it only accepts inputs through the default handle. If a first only handle is defined, the block will not accept input from the default handle on its first execution.

2. The condition block decides whether to proceed with true or false using either the detect max iteration feature or an expression. When using detect max iteration, it proceeds with true if the preceding blocks have reached their max iteration and have been skipped; otherwise, it proceeds with false.

- Therefore, if you place two person job blocks with max_iterations=2 and connect them to a condition block set to detect max iteration, you can implement a loop that runs twice.

## Key Features

### Dependency Management
- Topological sorting for optimal execution order
- Cycle detection with loop controller
- First-only handle logic for PersonJob nodes
- Condition branching with true/false paths

### Execution Context
```typescript
interface ExecutionContext {
  nodeOutputs: Record<string, any>;           // Results from each node
  nodeExecutionCounts: Record<string, number>; // Iteration tracking
  conditionValues: Record<string, boolean>;    // Branch decisions
  firstOnlyConsumed: Record<string, boolean>;  // First-only tracking
  executionOrder: string[];                    // Execution sequence
  totalCost: number;                          // Aggregated costs
}
```

### Advanced Controls
- **Loop Management**: Max iteration enforcement per node
- **Skip Management**: Centralized skip logic with reasons
- **Streaming Updates**: Real-time execution via SSE
- **Error Handling**: Continue-on-error in debug mode

## Backend API Endpoints

### Node Operations (Server-Only)
- `POST /api/nodes/personjob/execute` - LLM calls with person config
- `POST /api/nodes/db/execute` - File operations and data sources
- `POST /api/nodes/endpoint/execute` - File saving operations

### Diagram Execution
- `POST /api/run-diagram` - Full backend execution with SSE streaming
- `GET /api/monitor/stream` - SSE endpoint for execution monitoring

## CLI Tool Integration

The Python CLI tool leverages frontend execution logic via Node.js:

```bash
# Build the CLI runner (required after frontend changes)
pnpm build:cli

# Hybrid execution (recommended)
python tool.py run-and-monitor diagram.json

# Execution modes
python tool.py run diagram.json           # Hybrid with fallback
python tool.py run-headless diagram.json  # Pure backend execution
```

**Execution Strategy:**
- Client-safe nodes execute locally for performance
- Server-only nodes make targeted API calls to backend
- Automatic fallback to pure backend if Node.js unavailable

## Benefits

- **Security**: Sensitive operations (LLM APIs, file system) stay server-side
- **Performance**: Local execution where safe, reducing network overhead
- **Flexibility**: Works across browser, CLI, and pure backend scenarios
- **Resilience**: Graceful fallback strategies for different environments

## File Locations

### Frontend Execution Engine
- `apps/web/src/execution/execution-orchestrator.ts`
- `apps/web/src/execution/core/execution-engine.ts`
- `apps/web/src/execution/executors/`

### CLI Integration
- `tool.py` - Python CLI with hybrid execution
- `execution_runner.cjs` - Generated Node.js bundle (run `pnpm build:cli`)
- `apps/web/src/engine/cli-runner.ts` - CLI entry point source
- `esbuild.config.cjs` - Build configuration

### Backend API
- `apps/server/src/api/routers/` - API endpoint implementations
- `apps/server/src/services/` - Core business logic services