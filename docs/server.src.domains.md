# Backend Development Guide - Domains

## Architecture Overview

The backend follows Domain-Driven Design (DDD) with clear separation of concerns:

```
src/domains/
├── diagram/        # Diagram models, converters, and services
├── execution/      # Workflow execution engine
├── llm/           # LLM service adapters (OpenAI, Anthropic, etc.)
├── person/        # Agent memory management
└── integrations/  # External services (Notion)
```

## Core Concepts

### 1. Domain Models (`models/domain.py`)
Each domain defines its models using Pydantic for validation:

```python
from pydantic import BaseModel, Field
from src.shared.domain import NodeType, Vec2

class DomainNode(BaseModel):
    id: str
    type: NodeType
    position: Vec2
    data: Dict[str, Any] = Field(default_factory=dict)
```

### 2. Services Pattern
Services implement business logic with dependency injection:

```python
class DiagramService(BaseService, IDiagramService):
    def __init__(self, llm_service, api_key_service, memory_service):
        super().__init__()
        self.llm_service = llm_service
        # ...
```

### 3. Unified Executor System
The execution engine uses a registry-based pattern for node types:

```python
# Register node type
executor.register(NodeDefinition(
    type="person_job",
    schema=PersonJobProps,
    handler=person_job_handler,
    requires_services=["llm_service"],
))
```

## Key Domains

### Diagram Domain
Handles diagram serialization/deserialization with multiple formats:
- **Native JSON**: Full-fidelity GraphQL-compatible format
- **Light YAML**: Human-readable with labels instead of IDs
- **LLM YAML**: Optimized for AI understanding

```python
# Convert between formats
converter = converter_registry.get(DiagramFormat.LIGHT)
yaml_str = converter.serialize(diagram)
diagram = converter.deserialize(yaml_str)
```

### Execution Domain
Manages workflow execution with:
- **CompactEngine**: Core execution engine with topological sorting
- **Unified Executor**: Single executor handling all node types via handlers
- **Event Store**: Event-sourced execution state persistence

```python
# Execute diagram
async for event in execution_service.execute_diagram(
    diagram=diagram_dict,
    options={"continueOnError": False},
    execution_id=exec_id
):
    # Handle execution events
    pass
```

### LLM Domain
Provides unified interface for multiple LLM providers:

```python
# Create adapter
adapter = create_adapter("anthropic", "claude-3-5-sonnet", api_key)
result = await adapter.chat(system_prompt, user_prompt)
```

## Development Guidelines

### 1. Adding New Node Types

```python
# 1. Create schema (schemas/my_node.py)
class MyNodeProps(BaseNodeProps):
    my_field: str = Field(..., description="Required field")

# 2. Create handler (handlers/my_node_handler.py)
async def my_node_handler(props: MyNodeProps, context, inputs):
    # Implementation
    return {"output": result}

# 3. Register in registry
executor.register(NodeDefinition(
    type="my_node",
    schema=MyNodeProps,
    handler=my_node_handler
))
```

### 2. Service Interfaces
All services implement interfaces for dependency injection:

```python
from src.shared.interfaces import IFileService

class FileService(BaseService, IFileService):
    async def read(self, path: str) -> str:
        # Implementation
```

### 3. Error Handling
Use domain-specific exceptions:

```python
from src.shared.exceptions import DiagramExecutionError

if error_condition:
    raise DiagramExecutionError("Execution failed", {"node_id": node.id})
```

### 4. Memory Management
PersonJob nodes support conversation memory:

```python
# Memory is automatically managed
memory_service.add_message_to_conversation(
    content=response,
    sender_person_id=person_id,
    execution_id=execution_id,
    participant_person_ids=[person_id]
)
```

## Common Patterns

### Dependency Injection
```python
# app_context.py manages all services
def get_diagram_service() -> IDiagramService:
    return app_context.diagram_service
```

### Validation
```python
# Use Pydantic for validation
@field_validator('expression')
def validate_expression(cls, v):
    if not v:
        raise ValueError("Expression required")
    return v
```

### Token Usage Tracking
```python
token_usage = TokenUsage(
    input=100,
    output=50,
    cached=25
)
```

## Testing

```python
# Unit test handlers
async def test_handler():
    props = MyNodeProps(my_field="test")
    context = MockContext()
    result = await my_node_handler(props, context, {})
    assert result["output"] == expected
```

## Configuration

Environment variables:
- `USE_UNIFIED_EXECUTOR=true` - Enable new executor system
- `LOG_EXECUTOR_METRICS=true` - Enable metrics logging
- `API_KEY_STORE_FILE` - API key storage location
- `REDIS_URL` - Redis for distributed execution

## Quick Reference

**Key Base Classes**:
- `BaseService` - Common service functionality
- `BaseExecutor` - Executor interface
- `BaseNodeProps` - Node property validation
- `BaseAdapter` - LLM adapter interface

**Important Utilities**:
- `OutputProcessor` - Handle PersonJob outputs
- `DiagramValidator` - Validate diagram structure
- `TokenUsage` - Track LLM token usage
- `FeatureFlags` - Control feature rollout

**File Structure Convention**:
```
domain/
├── __init__.py       # Public API exports
├── models/          # Pydantic models
├── services/        # Business logic
├── converters/      # Format converters
└── handlers/        # Executor handlers
```