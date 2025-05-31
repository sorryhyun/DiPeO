# AgentDiagram Backend

FastAPI-based execution engine for visual LLM agent workflows with real-time streaming and conversation memory.

## Quick Start

```bash
cd apps/server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Visit http://localhost:8000/docs for API documentation.

## Architecture

```
src/
├── execution/         # Core execution engine
│   ├── executor.py    # Main diagram orchestrator
│   ├── nodes/         # Node type executors
│   └── state.py       # Execution state management
├── services/          # Business logic
│   ├── llm_service.py # Multi-provider LLM integration
│   └── memory_service.py # Conversation persistence
├── streaming/         # Real-time updates (SSE/WebSocket)
└── utils/            # Helpers and utilities
```

## Core Concepts

**Nodes**: Execution units (PersonJob, Condition, DB, Job, Start, Endpoint)  
**Arrows**: Data flow connections with content types (variable, raw_text, conversation_state)  
**Persons**: LLM agent configurations with memory  
**Dynamic Execution**: Condition-based branching and iteration support

## Loop rules

There is no special mechanism dedicated to loops, but a loop can be implemented using the following two mechanisms:

1. The person job block has an attribute called max_iteration. Once the block has been executed up to the number of times specified by max_iteration, it will be skipped for any subsequent requests. During this skipping, the forget rule does not apply, and all inputs are counted regardless of whether they were received via the first only handle or the default handle. For reference, the first only handle is used only for the initial execution of the block, after which it only accepts inputs through the default handle. If a first only handle is defined, the block will not accept input from the default handle on its first execution.

2. The condition block decides whether to proceed with true or false using either the detect max iteration feature or an expression. When using detect max iteration, it proceeds with true if the preceding blocks have reached their max iteration and have been skipped; otherwise, it proceeds with false.

Therefore, if you place two person job blocks with max_iterations=2 and connect them to a condition block set to detect max iteration, you can implement a loop that runs twice.


## Key Endpoints

| Endpoint | Purpose | Features |
|----------|---------|----------|
| `POST /api/run-diagram` | Execute with streaming | SSE real-time updates |
| `POST /api/run-diagram-sync` | Execute synchronously | Complete results |
| `GET /api/conversations` | Query conversation history | Pagination, filtering |
| `POST /api/apikeys` | Manage LLM API keys | Multi-provider support |
| `WS /ws/{client_id}` | WebSocket connection | Real-time execution monitoring |

## Execution Flow

1. **Validation** → Check diagram structure and dependencies
2. **Scheduling** → Topological sort with dynamic condition handling  
3. **Node Execution** → Process nodes in parallel where possible
4. **Memory Update** → Persist conversation context per person
5. **Stream Updates** → Real-time status via SSE/WebSocket

## Configuration

```env
BASE_DIR=/app                    # File operation root
MAX_CONCURRENT_NODES=10          # Parallel execution limit
REQUEST_TIMEOUT=300              # Node execution timeout (seconds)
REDIS_URL=redis://localhost:6379 # Optional: distributed memory
```

## Node Types

- **PersonJob**: LLM agent with conversation memory
- **Condition**: Boolean branching logic
- **DB**: File/code data sources
- **Job**: Stateless LLM operations or API calls
- **Start/Endpoint**: Execution boundaries

## Streaming Architecture

Unified streaming supports both SSE and WebSocket:
- SSE for simple client integration
- WebSocket for bidirectional communication
- Automatic fallback and queue management

## Security

- Path validation against `BASE_DIR`
- API key encryption at rest
- Rate limiting ready (implement in production)
- Sandboxed code execution for DB nodes

## Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Development

```bash
# Run with auto-reload
uvicorn main:app --reload

# Run tests
pytest tests/

# Check metrics
curl http://localhost:8000/metrics
```

## LLM Providers

Supported: OpenAI/ChatGPT, Anthropic/Claude, Google/Gemini, xAI/Grok

Adapters handle provider-specific APIs with unified interface and automatic retry logic.