# DiPeO, Diagrammed People (agents) & Organizations (agent system)
![image info](/image.png)

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


## Project Overview

DiPeO (Diagrammed People & Organizations) is a visual programming environment for building AI-powered agent workflows. It's a monorepo that enables users to create, execute, and monitor multi-agent systems through an intuitive drag-and-drop interface.

## Development Commands

### Frontend (React + TypeScript)
```bash
pnpm dev:web        # Start dev server on localhost:3000
pnpm build:web      # Production build
pnpm lint           # Run ESLint
pnpm lint:fix       # Fix linting issues
pnpm typecheck      # TypeScript type checking
pnpm analyze        # Bundle size analysis (from apps/web)
```

### Backend (FastAPI + Python)
```bash
# Always use python -m syntax for running the server
# IMPORTANT: Use WORKERS=1 for development to avoid WebSocket connection issues
WORKERS=1 python -m apps.server.main    # Development mode (single worker)
python -m apps.server.main              # Default: 4 workers (production)

# Alternative: Use the provided script
bash run-server.sh

# With hot reload
RELOAD=true python -m apps.server.main

# Note: Multiple workers create isolated ConnectionManager instances which
# breaks WebSocket connections if HTTP and WS requests hit different workers
```

### CLI Tool
```bash
# Run diagrams - always use tool.py
python tool.py run files/diagrams/diagram.json
python tool.py run files/diagrams/diagram.json --monitor
python tool.py run files/diagrams/diagram.json --debug --timeout=10

# Convert between formats
python tool.py convert input.yaml output.json

# Get diagram statistics
python tool.py stats diagram.json
```

### Testing
```bash
# Backend tests (limited coverage)
cd apps/server && python -m pytest

# Frontend tests: Not yet implemented
```

## Architecture Overview

### Key Concepts
- **Person-Based LLM Representation**: LLMs are represented as "persons" who maintain memory across tasks
- **Handle System**: Connections are made between specific handles (format: `nodeId:handleName`), not between nodes directly
- **WebSocket Execution**: Real-time execution with pause/resume/skip capabilities
- **Memory Management**: 3D underground space metaphor with 1000 message limit and 24h TTL

### Node Types
- `start`: Entry point with static data
- `person_job`: LLM tasks with memory management
- `condition`: Branching logic
- `job`: Code execution (Python/JS/Bash)
- `endpoint`: Terminal operations
- `db`: Data operations/file I/O
- `user_response`: Interactive prompts
- `notion`: Notion integration

### Directory Structure
```
apps/
├── server/          # FastAPI backend
│   ├── src/
│   │   ├── api/     # REST & WebSocket routes
│   │   ├── engine/  # Execution engine & executors
│   │   ├── llm/     # LLM provider adapters
│   │   └── services/# Business logic services
│   └── requirements.txt
└── web/            # React frontend
    ├── src/
    │   ├── components/  # UI components
    │   ├── hooks/      # React hooks
    │   ├── stores/     # Zustand state management
    │   ├── types/      # TypeScript types
    │   └── utils/      # Utilities & converters
    └── package.json
```

### Important File Locations
- Diagrams: `/files/diagrams/`
- Conversation logs: `/files/conversation_logs/`
- Results: `/files/results/`
- Uploads: `/files/uploads/`

## Development Guidelines

### Package Management
- **ALWAYS use `pnpm`** - never use `npm`, `npx`, or `node` commands
- This is a pnpm workspace-based monorepo

### LLM Configuration
- Always use `gpt-4.1-nano` for OpenAI LLM model
- API key "APIKEY_387B73" is safe for testing

### Code Search
- When using ripgrep: `--type ts` will find both `.ts` and `.tsx` files
- Do NOT use `--type tsx` (it doesn't exist)

### State Management
- Frontend uses Zustand v5 with unified store pattern
- Store is located at `apps/web/src/stores/unifiedStore.ts`
- Use selector factory pattern for performance

### WebSocket Communication
- WebSocket client: `apps/web/src/utils/websocket/client.ts`
- Event bus pattern for message handling
- Execution control via WebSocket messages

### Converter System
The converter system follows a two-stage conversion pipeline:

#### Conversion Flow
- **Import**: Format → Domain → Store (React-compatible)
- **Export**: Store → Domain → Format

#### Core Components
- **StoreDomainConverter** (`apps/web/src/utils/converters/core/storeDomainConverter.ts`)
  - Converts between React store (Maps) and domain format (Records)
  - Store format: Uses Maps for React Flow compatibility
  - Domain format: Uses Records for serialization

- **Format Converters** (`apps/web/src/utils/converters/formats/`)
  - `native-yaml`: Stores domain diagram as-is (full fidelity)
  - `light-yaml`: Simplified format using labels instead of IDs
  - `readable-yaml`: Human-friendly format with embedded connections
  - `llm-domain-yaml`: Optimized for AI understanding

- **Registry System** (`apps/web/src/utils/converters/core/registry.ts`)
  - Centralized converter registration
  - Format metadata management
  - Runtime converter lookup

#### Usage Example
```typescript
// Import flow
const converter = converterRegistry.get(format);
const domainDiagram = converter.deserialize(content);  // Format → Domain
const storeData = storeDomainConverter.domainToStore(domainDiagram);  // Domain → Store

// Export flow
const domainDiagram = storeDomainConverter.storeToDomain(storeState);  // Store → Domain
const content = converter.serialize(domainDiagram);  // Domain → Format
```

## Testing & Quality

### Code Quality
```bash
pnpm lint:fix      # Auto-fix linting issues
pnpm typecheck     # Ensure type safety
```

### Development Notes
- Project is in active development - backward compatibility not required
- Recent refactoring in progress (check git status)
- Use `dev` branch for development, `main` for PRs
- No comprehensive test suite yet - testing infrastructure needs implementation