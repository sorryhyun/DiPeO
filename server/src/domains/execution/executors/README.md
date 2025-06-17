# Unified Executor System

## Overview

The DiPeO executor system has been refactored to use a unified, declarative approach with Pydantic schemas and protocol-based handlers. This provides better type safety, maintainability, and extensibility.

## Architecture

### Core Components

1. **Unified Executor** (`unified_executor.py`): Single executor class that handles all node types
2. **Node Schemas** (`schemas/`): Pydantic models for node property validation
3. **Node Handlers** (`handlers/`): Business logic separated from execution framework
4. **Middleware** (`middleware/`): Cross-cutting concerns like logging, metrics, and error handling
5. **Registry** (`registry.py`): Node type registration and executor configuration

### Benefits

- **Type Safety**: Compile-time validation with Pydantic
- **Maintainability**: Clear separation of concerns
- **Testability**: Easy to unit test handlers in isolation
- **Extensibility**: Simple to add new node types
- **Observability**: Built-in metrics and logging

## Migration Guide

### Enabling the Unified Executor

The system supports both legacy and unified executors for gradual migration:

```bash
# Enable unified executor via environment variable
export USE_UNIFIED_EXECUTOR=true

# Or in your .env file
USE_UNIFIED_EXECUTOR=true
```

### Configuration Options

```bash
# Enable/disable unified executor (default: false)
USE_UNIFIED_EXECUTOR=true

# Enable executor metrics logging (default: true)
LOG_EXECUTOR_METRICS=true

# Enable detailed executor logging (default: false)
LOG_EXECUTOR_DETAILS=true

# Error handling configuration
EXECUTOR_MAX_RETRIES=3
EXECUTOR_RETRY_DELAY=1.0
EXECUTOR_ERROR_RATE_THRESHOLD=0.5
```

### Adding a New Node Type

1. **Create Schema** (`schemas/my_node.py`):
```python
from pydantic import BaseModel, Field

class MyNodeProps(BaseModel):
    my_field: str = Field(..., description="Required field")
    optional_field: int = Field(42, description="Optional with default")
```

2. **Create Handler** (`handlers/my_node_handler.py`):
```python
async def my_node_handler(props: MyNodeProps, context: ExecutionContext, inputs: Dict[str, Any]) -> Any:
    # Implementation
    return {"output": result}
```

3. **Register in Registry** (`registry.py`):
```python
executor.register(NodeDefinition(
    type="my_node",
    schema=MyNodeProps,
    handler=my_node_handler,
    requires_services=["file_service"],  # Optional
    description="My custom node type"
))
```

## Node Types

### Implemented Node Types

- **start**: Entry point with initial data
- **person_job**: LLM tasks with memory management
- **person_batch_job**: Batch LLM processing
- **condition**: Boolean logic and branching
- **job**: Safe code execution (Python/JS/Bash)
- **db**: File operations and data sources
- **endpoint**: Terminal operations with file saving
- **user_response**: Interactive user prompts
- **notion**: Notion API integration

### Middleware Components

1. **LoggingMiddleware**: Comprehensive execution logging
   - Pre/post execution events
   - Structured logging with metadata
   - Sensitive data sanitization

2. **MetricsMiddleware**: Performance and usage tracking
   - Execution counts and timings
   - Success/error rates
   - Token usage tracking
   - Per-node-type metrics

3. **ErrorHandlingMiddleware**: Advanced error handling
   - Retry logic for transient errors
   - Circuit breaker pattern
   - Error rate monitoring
   - Configurable error callbacks

## Testing

The unified executor is designed for easy testing:

```python
# Unit test a handler
async def test_my_handler():
    props = MyNodeProps(my_field="test")
    context = MockContext()
    inputs = {"input1": "value1"}
    
    result = await my_node_handler(props, context, inputs)
    assert result["output"] == expected_value

# Integration test with unified executor
async def test_unified_executor():
    executor = create_executor()
    node = {"id": "test1", "type": "my_node", "properties": {...}}
    context = TestContext()
    
    result = await executor.execute(node, context)
    assert result.error is None
```

## Performance

The unified executor provides several performance benefits:

- Reduced overhead from validation caching
- Parallel execution support
- Efficient middleware pipeline
- Optimized input resolution

## Backward Compatibility

The system maintains full backward compatibility:

- Legacy executors continue to work unchanged
- Gradual migration supported via feature flag
- Context adapter handles API differences
- No changes required to existing diagrams

## Future Enhancements

- Dynamic node type registration
- Plugin system for custom nodes
- Advanced caching strategies
- Distributed execution support
- Real-time metrics dashboard