# DiPeO Backend Development Guide

## Architecture Overview

DiPeO backend is a **FastAPI-based execution engine** for visual AI agent workflows, using **WebSocket connections** for real-time, bidirectional control.

```
┌────────────┐     ┌─────────┐
│   React Client        │ ─▶│  WebSocket API  │
└────────────┘     └─────────┘
                                        │
                            ┌─────▼────┐
                             │ Execution Engine│
                             └────┬─────┘
                                       │
                ┌───────────┴──────┐
                │                                  │
        ┌────▼─────┐           ┌─────▼───┐
        │ Node Executors    │           │ Domain Services │
        └──────────┘           └─────────┘
```

## Core Components

### 1. WebSocket Handler (`/api/routers/websocket.py`)
**All diagram execution flows through WebSocket** - no REST endpoints for execution.

```python
# Message types handled:
- execute_diagram    # Start execution with diagram JSON
- pause_execution   # Pause running execution
- resume_execution  # Resume paused execution
- user_response     # Provide input for user_response nodes
- broadcast_event   # CLI tool integration
```

### 2. Unified Execution Engine
Located in `/src/domains/execution/`, provides:
- **Topological sorting** for dependency resolution
- **Parallel execution** where possible
- **Skip management** for conditional flows
- **Memory persistence** across person interactions

### 3. Node Executors
Each node type has a dedicated executor in `/src/domains/execution/executors/`:

| Node Type | Purpose | Key Responsibility |
|-----------|---------|-------------------|
| `start` | Entry point | Provides initial data |
| `condition` | Branching | Boolean logic & loop detection |
| `job` | Code execution | Sandboxed Python/JS/Bash |
| `person_job` | LLM interaction | Context-aware AI calls |
| `person_batch_job` | Batch LLM ops | Parallel processing |
| `db` | Data operations | File/collection I/O |
| `endpoint` | Output | File writing & results |
| `user_response` | User input | Interactive prompts |
| `notion` | Notion API | Page/database operations |

## Domain-Driven Design Structure

```
apps/server/src/
├── domains/
│   ├── execution/      # Core execution logic
│   │   ├── engine.py   # Main orchestrator
│   │   └── executors/  # Node type handlers
│   ├── llm/           # LLM integrations
│   ├── memory/        # Conversation persistence
│   └── storage/       # File & data management
├── interfaces/
│   ├── api/          # HTTP/WebSocket endpoints
│   └── graphql/      # GraphQL schema (future)
└── common/
    ├── context.py    # Application context
    └── exceptions.py # Error handling
```

## Key Services

### LLMService
Provides unified interface for multiple providers:
```python
# Supported: openai, claude, gemini, grok
await llm_service.chat(
    service="openai",
    model="gpt-4.1-nano",
    messages=[...],
    api_key="..."
)
```

### MemoryService
Manages conversation history per person:
```python
# Thread-based memory isolation
await memory_service.add_message(thread_id, message)
history = await memory_service.get_history(thread_id)
```

### FileService
Handles diagram and file operations:
```python
# Auto-detects format from extension
diagram = await file_service.load_diagram("workflow.yaml")
await file_service.save_output(execution_id, data)
```

## Architectural Improvements

### 1. **Stronger Type Safety**
```python
# Current: Dict[str, Any] everywhere
# Better: Use Pydantic models consistently

from pydantic import BaseModel
from typing import Literal

class NodeExecution(BaseModel):
    node_id: str
    node_type: Literal["start", "condition", ...]
    inputs: Dict[str, Any]
    execution_count: int = 0

class ExecutionState(BaseModel):
    execution_id: str
    diagram: DiagramModel
    node_states: Dict[str, NodeExecution]
    outputs: Dict[str, Any]
```

### 2. **Event-Driven Architecture**
Replace direct WebSocket handling with event bus:

```python
# Event bus for decoupling
class ExecutionEventBus:
    async def emit(self, event: ExecutionEvent):
        # Distribute to handlers
        
    async def on(self, event_type: str, handler: Callable):
        # Register handlers

# Usage
bus = ExecutionEventBus()
bus.on("node_completed", handle_node_completion)
bus.on("execution_paused", handle_pause)
```

### 3. **Dependency Injection Consistency**
Current code mixes manual service creation with DI. Standardize on FastAPI's DI:

```python
# Consistent dependency injection
async def execute_node(
    node: Node,
    llm: LLMService = Depends(get_llm_service),
    memory: MemoryService = Depends(get_memory_service)
):
    # All services injected, no manual creation
```

### 4. **Executor Registry Pattern**
Make node executor registration more dynamic:

```python
class ExecutorRegistry:
    _executors: Dict[str, Type[BaseExecutor]] = {}
    
    @classmethod
    def register(cls, node_type: str):
        def decorator(executor: Type[BaseExecutor]):
            cls._executors[node_type] = executor
            return executor
        return decorator
    
    @classmethod
    def get_executor(cls, node_type: str) -> BaseExecutor:
        return cls._executors[node_type]()

# Usage
@ExecutorRegistry.register("person_job")
class PersonJobExecutor(BaseExecutor):
    pass
```

### 5. **Context Management**
Simplify the execution context:

```python
class ExecutionContext:
    """Immutable execution context"""
    
    def with_node(self, node_id: str) -> 'ExecutionContext':
        """Create new context for node execution"""
        return ExecutionContext(
            **{**self.__dict__, 'current_node': node_id}
        )
    
    def get_upstream_outputs(self, node_id: str) -> Dict[str, Any]:
        """Get outputs from upstream nodes"""
        # Graph traversal logic
```

## Best Practices

### 1. **Error Handling**
```python
# Use domain-specific exceptions
class NodeExecutionError(Exception):
    def __init__(self, node_id: str, error: str):
        self.node_id = node_id
        super().__init__(f"Node {node_id}: {error}")

# Wrap executor calls
try:
    result = await executor.execute(node, context)
except Exception as e:
    raise NodeExecutionError(node.id, str(e))
```

### 2. **Async/Await Consistency**
- Always use `async def` for I/O operations
- Use `asyncio.gather()` for parallel node execution
- Avoid blocking calls in async functions

### 3. **WebSocket Message Standards**
```python
class WSMessage(BaseModel):
    type: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
```

### 4. **Configuration Management**
```python
# Use Pydantic settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    port: int = 8000
    workers: int = 4
    log_level: str = "INFO"
    redis_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
```

## Testing Strategy

### 1. **Unit Tests**
```python
# Test executors in isolation
async def test_condition_executor():
    executor = ConditionExecutor()
    context = MockContext(...)
    result = await executor.execute(node, context)
    assert result.output in ["true", "false"]
```

### 2. **Integration Tests**
```python
# Test full execution flow
async def test_diagram_execution():
    async with websockets.connect("ws://localhost:8000/api/ws") as ws:
        await ws.send(json.dumps({
            "type": "execute_diagram",
            "diagram": test_diagram
        }))
        # Assert execution events
```

### 3. **Performance Tests**
- Test parallel node execution
- Measure WebSocket message latency
- Profile memory usage with large diagrams

## Development Workflow

### 1. **Adding a New Node Type**
1. Define executor in `/src/domains/execution/executors/`
2. Register in executor factory
3. Add validation schema
4. Update frontend config in `/apps/web/src/config/`
5. Add tests

### 2. **Adding a New LLM Provider**
1. Create adapter in `/src/domains/llm/adapters/`
2. Implement `chat()` method
3. Register in LLM factory
4. Add provider-specific error handling

### 3. **Debugging Executions**
```python
# Enable debug mode for detailed logs
logger.setLevel(logging.DEBUG)

# Use execution IDs to trace flows
grep "exec_abc123" logs/server.log

# Monitor WebSocket messages
wscat -c ws://localhost:8000/api/ws
```

## Performance Optimization

### 1. **Caching**
- Cache LLM responses by hash(prompt + model)
- Cache file reads for repeated access
- Use Redis for multi-worker deployments

### 2. **Connection Pooling**
```python
# Reuse HTTP clients
class LLMAdapter:
    _client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=100)
    )
```

### 3. **Batch Operations**
- Group multiple LLM calls when possible
- Batch database writes
- Use `asyncio.gather()` for parallel I/O

## Monitoring & Observability

### 1. **Metrics** (via `/metrics`)
- Execution count by node type
- Average execution time
- Error rates
- Token usage

### 2. **Logging**
```python
logger.info(
    "Node executed",
    extra={
        "execution_id": ctx.execution_id,
        "node_id": node.id,
        "duration_ms": duration
    }
)
```

### 3. **Tracing**
Consider OpenTelemetry for distributed tracing across WebSocket connections.

## Security Considerations

1. **API Key Management**
   - Never log API keys
   - Validate keys before use
   - Support key rotation

2. **Code Execution Sandboxing**
   - Use restricted Python environments
   - Limit resource usage
   - Sanitize user code

3. **WebSocket Security**
   - Implement rate limiting
   - Add connection authentication
   - Validate message schemas

## Future Enhancements

1. **GraphQL API** - Schema already defined, needs implementation
2. **Distributed Execution** - Redis-backed job queue
3. **Version Control** - Diagram versioning and rollback
4. **A2A Canvas** - Agent-to-agent communication
5. **Advanced Memory** - Vector embeddings for context retrieval