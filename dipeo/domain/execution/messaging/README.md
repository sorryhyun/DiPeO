# Message Envelope System

## Overview

The `Envelope` system provides a standardized, immutable message format for inter-node communication in DiPeO. All data flowing between nodes is wrapped in `Envelope` objects, which carry:

- Content with explicit type information
- Metadata (iteration, branch, timestamps)
- Error information
- Tracing data

## Core Concepts

### Why Envelopes?

**Problem:** Nodes produce different output types (text, JSON, binary, conversation state). Without a standard format:
- Type mismatches cause runtime errors
- No consistent error handling
- Metadata (iteration, branch) requires ad-hoc conventions
- Difficult to trace data flow

**Solution:** Wrap all outputs in `Envelope` with explicit `ContentType`:
```python
# Instead of raw values
output = "some text"

# Use envelopes
output = Envelope(
    body="some text",
    content_type=ContentType.RAW_TEXT,
    produced_by=node_id
)
```

### Immutability

Envelopes are **immutable** (frozen dataclass). Operations that "modify" an envelope return a new instance:

```python
# Add metadata - returns NEW envelope
env2 = env1.with_meta(iteration=5)

# Original unchanged
assert env1.meta == {}
assert env2.meta == {"iteration": 5}
```

This enables:
- Safe sharing across nodes
- Concurrent access without locks
- Clear data lineage
- Functional programming style

## Envelope Structure

**Location:** `dipeo/domain/execution/messaging/envelope.py:21`

```python
@dataclass(frozen=True)
class Envelope:
    """Immutable message envelope for inter-node communication."""

    id: str = field(default_factory=lambda: str(uuid4()))
    trace_id: str = field(default="")
    produced_by: str = field(default="system")
    content_type: ContentType = field(default="raw_text")
    schema_id: str | None = field(default=None)
    serialization_format: str | None = field(default=None)
    body: Any = field(default=None)
    meta: dict[str, Any] = field(default_factory=dict)
```

### Fields

**id: str**
- Unique identifier for this envelope
- Auto-generated UUID
- Used for tracing and debugging

**trace_id: str**
- Trace ID for distributed tracing
- Links envelopes across nodes
- Empty by default

**produced_by: str**
- Node ID that produced this envelope
- Used for debugging and lineage
- Defaults to "system"

**content_type: ContentType**
- Explicit content type (RAW_TEXT, OBJECT, BINARY, CONVERSATION_STATE)
- Used for type-safe data extraction
- Enables smart conversions

**schema_id: str | None**
- Optional schema identifier for validation
- Future: Pydantic model references
- Not currently used

**serialization_format: str | None**
- Optional format hint (json, yaml, msgpack)
- Not currently used

**body: Any**
- The actual payload
- Type should match content_type
- Can be None

**meta: dict[str, Any]**
- Arbitrary metadata
- Common keys: iteration, branch_id, timestamp, error
- Immutable dictionary (replaced on updates)

## Content Types

**From:** `dipeo.diagram_generated.enums.ContentType`

```python
class ContentType(Enum):
    RAW_TEXT = "raw_text"                    # str
    OBJECT = "object"                        # dict | list (JSON)
    BINARY = "binary"                        # bytes
    CONVERSATION_STATE = "conversation_state" # dict with messages/context
```

### RAW_TEXT

Plain text content.

```python
env = EnvelopeFactory.create(body="Hello world")
assert env.content_type == ContentType.RAW_TEXT

text = env.as_text()  # "Hello world"
```

### OBJECT

JSON-serializable objects (dict, list, primitives).

```python
env = EnvelopeFactory.create(body={"key": "value", "count": 42})
assert env.content_type == ContentType.OBJECT

data = env.as_json()  # {"key": "value", "count": 42}
```

### BINARY

Binary data (bytes, bytearray, memoryview).

```python
env = EnvelopeFactory.create(body=b"\x00\x01\x02", content_type=ContentType.BINARY)
data = env.as_bytes()  # b"\x00\x01\x02"
```

### CONVERSATION_STATE

Conversation context for LLM nodes (PersonJob).

```python
env = EnvelopeFactory.create(body={
    "messages": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"}
    ],
    "context": {"user_id": "123"}
})
assert env.content_type == ContentType.OBJECT  # Auto-detected, but treated specially
```

## EnvelopeFactory

**Location:** `dipeo/domain/execution/messaging/envelope.py:130`

Factory for creating envelopes with auto-detection and convenience methods.

### create()

```python
EnvelopeFactory.create(
    body: Any,
    content_type: ContentType | None = None,
    node_id: str | None = None,
    error: str | None = None,
    **kwargs
) -> Envelope
```

**Auto-detection:**
```python
# Automatically detects content type
text_env = EnvelopeFactory.create(body="text")           # RAW_TEXT
json_env = EnvelopeFactory.create(body={"key": "val"})   # OBJECT
bin_env = EnvelopeFactory.create(body=b"\x00")           # BINARY
```

**Explicit type:**
```python
env = EnvelopeFactory.create(
    body="some text",
    content_type=ContentType.RAW_TEXT,
    node_id="person-job-1"
)
```

**Error envelopes:**
```python
error_env = EnvelopeFactory.create(
    body="Division by zero",
    error="ValidationError",
    node_id="code-job-1"
)
assert error_env.has_error()
assert error_env.meta["error"] == "Division by zero"
assert error_env.meta["error_type"] == "ValidationError"
```

**With metadata:**
```python
env = EnvelopeFactory.create(
    body="value",
    meta={"iteration": 5, "custom": "data"}
)
```

## Content Extraction

### Safe Extraction (Strict)

These methods raise `TypeError` if content type doesn't match:

**to_text() -> str**
```python
text = envelope.to_text()  # Raises if not RAW_TEXT
```

**to_json() -> Any**
```python
data = envelope.to_json()  # Raises if not OBJECT
```

**to_bytes() -> bytes**
```python
data = envelope.to_bytes()  # Raises if not BINARY
```

### Permissive Extraction

These methods attempt conversion:

**as_text() -> str**
```python
# Works with RAW_TEXT
text = env.as_text()  # str
```

**as_json(model: type[T] | None = None) -> T | dict | list**
```python
# Works with OBJECT
data = env.as_json()  # dict | list

# With Pydantic validation
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

user = env.as_json(model=User)  # Validates against User model
```

**as_bytes() -> bytes**
```python
# Works with BINARY
data = env.as_bytes()  # bytes
```

**as_conversation() -> dict**
```python
# Works with CONVERSATION_STATE
conv = env.as_conversation()  # dict with messages/context
```

### Direct Access

**body: Any**
```python
# Direct access without type checking
value = envelope.body
```

Use when you know the type or don't care about validation.

## Metadata Operations

### with_meta(**kwargs) -> Envelope

Add or update metadata (returns new envelope):

```python
env1 = EnvelopeFactory.create(body="data")
env2 = env1.with_meta(iteration=5, branch="true")
env3 = env2.with_meta(timestamp=time.time())

# Original unchanged
assert env1.meta == {}
assert env2.meta == {"iteration": 5, "branch": "true"}
assert env3.meta == {"iteration": 5, "branch": "true", "timestamp": ...}
```

### with_iteration(iteration: int) -> Envelope

Convenience for loop iterations:

```python
env = envelope.with_iteration(5)
assert env.meta["iteration"] == 5
```

### with_branch(branch_id: str) -> Envelope

Convenience for condition branches:

```python
env = envelope.with_branch("condtrue")
assert env.meta["branch_id"] == "condtrue"
```

## Error Handling

### Creating Error Envelopes

```python
# Using factory
error_env = EnvelopeFactory.create(
    body="Error message",
    error="ValidationError",
    node_id="node-1"
)

# Manually
error_env = Envelope(
    body="Error message",
    content_type=ContentType.RAW_TEXT,
    meta={
        "is_error": True,
        "error": "Error message",
        "error_type": "ValidationError"
    }
)
```

### Checking for Errors

**has_error() -> bool**
```python
if envelope.has_error():
    print(f"Error: {envelope.error}")
```

**error property -> str | None**
```python
error_msg = envelope.error  # envelope.meta.get("error")
```

### Error Propagation

Errors flow through the graph as envelopes:

```python
# Node A fails
error = EnvelopeFactory.create(body="Failed", error="RuntimeError")
ctx.emit_outputs_as_tokens(node_a, {"default": error})

# Node B receives error envelope
inputs = ctx.consume_inbound(node_b)
if inputs["default"].has_error():
    # Handle or propagate
    pass
```

## Serialization

### Protocol Format

```python
from dipeo.domain.execution.messaging import serialize_protocol, deserialize_protocol

# Serialize
data = serialize_protocol(envelope)
# {
#     "envelope_format": True,
#     "id": "...",
#     "content_type": "raw_text",
#     "body": "...",
#     "meta": {...}
# }

# Deserialize
envelope = deserialize_protocol(data)
```

Used for:
- Persistence (future)
- Network transmission (future)
- GraphQL responses

## Usage Patterns

### Basic Flow

```python
# 1. Execute node
result = execute_node(node, inputs)

# 2. Wrap in envelope
output = EnvelopeFactory.create(
    body=result,
    node_id=node.id
)

# 3. Emit
ctx.emit_outputs_as_tokens(node.id, {"default": output})

# 4. Downstream node receives
inputs = ctx.consume_inbound(downstream_node.id)
envelope = inputs["default"]

# 5. Extract content
data = envelope.body
```

### Loop Iterations

```python
# Add iteration metadata
for i in range(10):
    result = execute_loop_body(i)
    output = EnvelopeFactory.create(body=result).with_iteration(i)
    ctx.emit_outputs_as_tokens(node.id, {"default": output})
```

### Condition Branches

```python
# Condition node emits on specific branches
if condition_result:
    output = EnvelopeFactory.create(body=True).with_branch("condtrue")
    ctx.emit_outputs_as_tokens(node.id, {"condtrue": output})
else:
    output = EnvelopeFactory.create(body=False).with_branch("condfalse")
    ctx.emit_outputs_as_tokens(node.id, {"condfalse": output})
```

### Error Handling

```python
try:
    result = execute_node(node, inputs)
    output = EnvelopeFactory.create(body=result, node_id=node.id)
except Exception as e:
    output = EnvelopeFactory.create(
        body=str(e),
        error=type(e).__name__,
        node_id=node.id
    )

ctx.emit_outputs_as_tokens(node.id, {"default": output})
```

## Design Rationale

### Why Immutable?

- **Safety**: No accidental modifications
- **Concurrency**: Safe to share across threads
- **Functional**: Pure functions, no side effects
- **Debugging**: Clear data lineage

### Why Explicit ContentType?

- **Type Safety**: Catch mismatches at runtime
- **Smart Conversions**: Enable automatic text ↔ JSON conversion
- **Documentation**: Self-documenting data flow
- **Validation**: Enable schema validation (future)

### Why Factory Pattern?

- **Convenience**: Auto-detect content type
- **Consistency**: Standard timestamps and IDs
- **Flexibility**: Easy to extend with new creation patterns

## Performance Considerations

- **Immutability**: New instances created for metadata updates (cheap for small objects)
- **UUID Generation**: Uses `uuid4()` per envelope (fast enough for execution flow)
- **Metadata Copying**: Shallow copy on `with_meta()` (dict copy)
- **Type Checking**: Minimal overhead (enum comparison)

## Related Components

- **Token** (`tokens/token_types.py`): Wraps Envelope for flow control
- **ExecutionContext** (`context/execution_context.py`): Manages envelope flow
- **resolve_inputs** (`resolution/api.py`): Extracts values from envelopes

## Future Enhancements

1. **Schema Validation**: Use `schema_id` to reference Pydantic models
2. **Compression**: Large payloads compressed in BINARY format
3. **Streaming**: Support for streaming content (files, audio)
4. **Versioning**: Envelope format versioning for backward compatibility
5. **Encryption**: Sensitive data encryption at rest
