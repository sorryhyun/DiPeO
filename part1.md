# Phase 1: Envelope Infrastructure Implementation Guide

## Overview
Introduce standardized message envelopes for node communication without breaking existing functionality.

## Step-by-Step Implementation

### Step 1: Create Core Envelope Classes (Day 1-2)

#### 1.1 Create `/dipeo/core/execution/envelope.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Any, Protocol
from uuid import uuid4
import time

ContentType = Literal["raw_text", "object", "conversation_state", "binary"]

@dataclass(frozen=True)
class Envelope:
    """Immutable message envelope for inter-node communication"""
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid4()))
    trace_id: str = field(default="")
    
    # Source
    produced_by: str = field(default="system")
    
    # Content
    content_type: ContentType = field(default="raw_text")
    schema_id: str | None = field(default=None)
    body: Any = field(default=None)
    
    # Metadata
    meta: dict[str, Any] = field(default_factory=dict)
    
    def with_meta(self, **kwargs) -> Envelope:
        """Create new envelope with updated metadata"""
        new_meta = {**self.meta, **kwargs}
        return dataclass.replace(self, meta=new_meta)
    
    def with_iteration(self, iteration: int) -> Envelope:
        """Tag with iteration number"""
        return self.with_meta(iteration=iteration)
    
    def with_branch(self, branch_id: str) -> Envelope:
        """Tag with branch identifier"""
        return self.with_meta(branch_id=branch_id)

class EnvelopeFactory:
    """Factory for creating envelopes"""
    
    @staticmethod
    def text(content: str, **kwargs) -> Envelope:
        return Envelope(
            content_type="raw_text",
            body=content,
            meta={"timestamp": time.time()},
            **kwargs
        )
    
    @staticmethod
    def json(data: Any, schema_id: str | None = None, **kwargs) -> Envelope:
        return Envelope(
            content_type="object",
            schema_id=schema_id,
            body=data,
            meta={"timestamp": time.time()},
            **kwargs
        )
    
    @staticmethod
    def conversation(state: dict, **kwargs) -> Envelope:
        return Envelope(
            content_type="conversation_state",
            body=state,
            meta={"timestamp": time.time()},
            **kwargs
        )
```

#### 1.2 Create `/dipeo/core/execution/envelope_reader.py`

```python
import json
from typing import Any, TypeVar, Type
from pydantic import BaseModel, ValidationError

from .envelope import Envelope, ContentType

T = TypeVar('T', bound=BaseModel)

class EnvelopeReader:
    """Safe extraction of envelope contents"""
    
    def as_text(self, envelope: Envelope) -> str:
        """Extract text content with automatic coercion"""
        if envelope.content_type == "raw_text":
            return str(envelope.body) if envelope.body is not None else ""
        elif envelope.content_type == "object":
            return json.dumps(envelope.body)
        elif envelope.content_type == "conversation_state":
            # Extract text from conversation
            if isinstance(envelope.body, dict):
                return envelope.body.get("last_message", "")
            return str(envelope.body)
        else:
            raise ValueError(f"Cannot convert {envelope.content_type} to text")
    
    def as_json(
        self, 
        envelope: Envelope, 
        model: Type[T] | None = None
    ) -> T | dict | list:
        """Extract and optionally validate JSON content"""
        if envelope.content_type != "object":
            # Try to parse text as JSON
            if envelope.content_type == "raw_text":
                try:
                    data = json.loads(envelope.body)
                except (json.JSONDecodeError, TypeError):
                    raise ValueError(f"Cannot parse text as JSON: {envelope.body[:100]}")
            else:
                raise ValueError(f"Cannot extract JSON from {envelope.content_type}")
        else:
            data = envelope.body
        
        # Validate with Pydantic if model provided
        if model:
            try:
                return model.model_validate(data)
            except ValidationError as e:
                raise ValueError(f"Schema validation failed: {e}")
        
        return data
    
    def as_conversation(self, envelope: Envelope) -> dict:
        """Extract conversation state"""
        if envelope.content_type != "conversation_state":
            raise ValueError(f"Expected conversation_state, got {envelope.content_type}")
        return envelope.body
    
    def as_binary(self, envelope: Envelope) -> bytes:
        """Extract binary content"""
        if envelope.content_type != "binary":
            # Try to encode text as bytes
            if envelope.content_type == "raw_text":
                return envelope.body.encode('utf-8')
            else:
                raise ValueError(f"Cannot extract binary from {envelope.content_type}")
        return envelope.body
    
    def get_meta(self, envelope: Envelope, key: str, default: Any = None) -> Any:
        """Safely get metadata value"""
        return envelope.meta.get(key, default)
```

### Step 2: Create Legacy Adapter (Day 3)

#### 2.1 Create `/dipeo/application/execution/envelope_adapter.py`

```python
from typing import Any
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from dipeo.core.execution.node_output import NodeOutput

class EnvelopeAdapter:
    """Bridge between legacy dict outputs and envelopes"""
    
    @staticmethod
    def from_legacy_output(
        output: Any,
        node_id: str = "unknown",
        trace_id: str = ""
    ) -> list[Envelope]:
        """Convert various legacy output formats to envelopes"""
        
        # Handle NodeOutput objects
        if isinstance(output, NodeOutput):
            if hasattr(output, 'as_envelopes'):
                return output.as_envelopes()
            
            # Extract from success/error format
            if output.success:
                content = output.data
            else:
                content = {"error": str(output.error)}
                
            return [EnvelopeAdapter._create_envelope(content, node_id, trace_id)]
        
        # Handle direct values
        return [EnvelopeAdapter._create_envelope(output, node_id, trace_id)]
    
    @staticmethod
    def _create_envelope(content: Any, node_id: str, trace_id: str) -> Envelope:
        """Create appropriate envelope based on content type"""
        
        if content is None:
            return EnvelopeFactory.text("", produced_by=node_id, trace_id=trace_id)
        elif isinstance(content, str):
            return EnvelopeFactory.text(content, produced_by=node_id, trace_id=trace_id)
        elif isinstance(content, (dict, list)):
            return EnvelopeFactory.json(content, produced_by=node_id, trace_id=trace_id)
        elif isinstance(content, bytes):
            return Envelope(
                content_type="binary",
                body=content,
                produced_by=node_id,
                trace_id=trace_id
            )
        else:
            # Fallback: convert to string
            return EnvelopeFactory.text(str(content), produced_by=node_id, trace_id=trace_id)
    
    @staticmethod
    def to_legacy_input(envelope: Envelope) -> Any:
        """Convert envelope back to expected legacy format"""
        
        if envelope.content_type == "raw_text":
            return envelope.body
        elif envelope.content_type == "object":
            return envelope.body
        elif envelope.content_type == "conversation_state":
            # Return the raw conversation state
            return envelope.body
        elif envelope.content_type == "binary":
            return envelope.body
        else:
            return envelope.body
    
    @staticmethod
    def wrap_handler_output(
        handler_result: Any,
        node_id: str,
        trace_id: str
    ) -> NodeOutput:
        """Wrap handler result with envelope support"""
        
        if isinstance(handler_result, NodeOutput):
            # Enhance existing NodeOutput with envelope support
            if not hasattr(handler_result, 'as_envelopes'):
                envelopes = EnvelopeAdapter.from_legacy_output(
                    handler_result, node_id, trace_id
                )
                handler_result._envelopes = envelopes
            return handler_result
        
        # Create new NodeOutput with envelopes
        envelopes = EnvelopeAdapter.from_legacy_output(
            handler_result, node_id, trace_id
        )
        output = NodeOutput.success(data=handler_result)
        output._envelopes = envelopes
        return output
```

### Step 3: Update NodeOutput Protocol (Day 4)

#### 3.1 Modify `/dipeo/core/execution/node_output.py`

```python
# Add to existing NodeOutput class

from typing import Protocol
from dipeo.core.execution.envelope import Envelope

class NodeOutputProtocol(Protocol):
    """Protocol for node execution outputs"""
    
    @property
    def success(self) -> bool:
        """Whether execution succeeded"""
        ...
    
    @property
    def data(self) -> Any:
        """Output data (legacy)"""
        ...
    
    def as_envelopes(self) -> list[Envelope]:
        """Convert to standardized envelopes"""
        ...
    
    def primary_envelope(self) -> Envelope:
        """Get primary output envelope"""
        ...

class NodeOutput:
    """Concrete implementation with envelope support"""
    
    def __init__(self, success: bool, data: Any = None, error: Exception | None = None):
        self.success = success
        self.data = data
        self.error = error
        self._envelopes: list[Envelope] | None = None
    
    def as_envelopes(self) -> list[Envelope]:
        """Convert to envelopes lazily"""
        if self._envelopes is None:
            from dipeo.application.execution.envelope_adapter import EnvelopeAdapter
            self._envelopes = EnvelopeAdapter.from_legacy_output(
                self.data if self.success else {"error": str(self.error)},
                node_id="unknown",
                trace_id=""
            )
        return self._envelopes
    
    def primary_envelope(self) -> Envelope:
        """Get first/primary envelope"""
        envelopes = self.as_envelopes()
        if not envelopes:
            # Return empty envelope if none exist
            from dipeo.core.execution.envelope import EnvelopeFactory
            return EnvelopeFactory.text("")
        return envelopes[0]
    
    def with_envelopes(self, envelopes: list[Envelope]) -> 'NodeOutput':
        """Set explicit envelopes"""
        self._envelopes = envelopes
        return self
```

### Step 4: Integration Points (Day 5-7)

#### 4.1 Update TypedExecutionEngine to use envelopes

```python
# In /dipeo/application/execution/typed_engine.py

async def _execute_node(
    self,
    node: ExecutableNode,
    context: TypedExecutionContext,
    diagram: ExecutableDiagram
) -> None:
    """Execute single node with envelope support"""
    
    trace_id = context.execution_id
    
    try:
        # Get handler
        handler = self._get_handler(node)
        
        # Create request
        request = ExecutionRequest(
            node=node,
            context=context,
            diagram=diagram,
            trace_id=trace_id
        )
        
        # Execute
        result = await handler.execute_request(request)
        
        # Ensure result has envelopes
        if not hasattr(result, 'as_envelopes'):
            from dipeo.application.execution.envelope_adapter import EnvelopeAdapter
            result = EnvelopeAdapter.wrap_handler_output(
                result, node.id, trace_id
            )
        
        # Store envelopes in context
        for envelope in result.as_envelopes():
            context.store_output(node.id, envelope)
        
        # Emit events
        await self._emit_node_completed(node, result)
        
    except Exception as e:
        # Wrap error in envelope
        error_envelope = EnvelopeFactory.json(
            {"error": str(e), "type": type(e).__name__},
            produced_by=node.id,
            trace_id=trace_id
        )
        context.store_output(node.id, error_envelope)
        await self._emit_node_failed(node, e)
```

#### 4.2 Update RuntimeResolver to work with envelopes

```python
# In /dipeo/application/execution/resolvers/standard_runtime_resolver.py

async def resolve_node_inputs(
    self,
    node: ExecutableNode,
    context: TypedExecutionContext,
    diagram: ExecutableDiagram
) -> dict[str, Any]:
    """Resolve inputs with envelope support"""
    
    # Check if handler expects envelopes
    handler = self._get_handler(node)
    expects_envelopes = getattr(handler, '_expects_envelopes', False)
    
    resolved = {}
    
    for edge in self._get_incoming_edges(node, diagram):
        # Get source output as envelope
        source_output = context.get_output(edge.source_id)
        
        if isinstance(source_output, Envelope):
            envelope = source_output
        else:
            # Convert legacy output to envelope
            from dipeo.application.execution.envelope_adapter import EnvelopeAdapter
            envelopes = EnvelopeAdapter.from_legacy_output(
                source_output,
                node_id=edge.source_id,
                trace_id=context.execution_id
            )
            envelope = envelopes[0] if envelopes else None
        
        if envelope:
            # Store envelope or convert to legacy format
            if expects_envelopes:
                resolved[edge.label or 'default'] = envelope
            else:
                # Convert back to legacy for compatibility
                from dipeo.application.execution.envelope_adapter import EnvelopeAdapter
                resolved[edge.label or 'default'] = EnvelopeAdapter.to_legacy_input(envelope)
    
    return resolved
```

### Step 5: Testing (Day 8-10)

#### 5.1 Create `/dipeo/tests/refactoring/test_envelopes.py`

```python
import pytest
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from dipeo.core.execution.envelope_reader import EnvelopeReader
from dipeo.application.execution.envelope_adapter import EnvelopeAdapter

class TestEnvelope:
    def test_envelope_creation(self):
        envelope = EnvelopeFactory.text("Hello")
        assert envelope.content_type == "raw_text"
        assert envelope.body == "Hello"
        assert "timestamp" in envelope.meta
    
    def test_envelope_immutability(self):
        envelope = EnvelopeFactory.text("Test")
        with pytest.raises(AttributeError):
            envelope.body = "Modified"
    
    def test_envelope_with_meta(self):
        envelope = EnvelopeFactory.text("Test")
        updated = envelope.with_meta(custom="value")
        assert updated.meta["custom"] == "value"
        assert envelope.meta.get("custom") is None  # Original unchanged

class TestEnvelopeReader:
    def setup_method(self):
        self.reader = EnvelopeReader()
    
    def test_as_text_from_text(self):
        envelope = EnvelopeFactory.text("Hello")
        assert self.reader.as_text(envelope) == "Hello"
    
    def test_as_text_from_json(self):
        envelope = EnvelopeFactory.json({"key": "value"})
        text = self.reader.as_text(envelope)
        assert "key" in text
        assert "value" in text
    
    def test_as_json_from_object(self):
        data = {"test": 123}
        envelope = EnvelopeFactory.json(data)
        assert self.reader.as_json(envelope) == data
    
    def test_as_json_with_validation(self):
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            age: int
        
        envelope = EnvelopeFactory.json({"name": "Alice", "age": 30})
        result = self.reader.as_json(envelope, TestModel)
        assert isinstance(result, TestModel)
        assert result.name == "Alice"
        assert result.age == 30

class TestEnvelopeAdapter:
    def test_from_legacy_string(self):
        envelopes = EnvelopeAdapter.from_legacy_output("Hello", "node1", "trace1")
        assert len(envelopes) == 1
        assert envelopes[0].content_type == "raw_text"
        assert envelopes[0].body == "Hello"
    
    def test_from_legacy_dict(self):
        data = {"key": "value"}
        envelopes = EnvelopeAdapter.from_legacy_output(data, "node1", "trace1")
        assert len(envelopes) == 1
        assert envelopes[0].content_type == "object"
        assert envelopes[0].body == data
    
    def test_to_legacy_text(self):
        envelope = EnvelopeFactory.text("Hello")
        legacy = EnvelopeAdapter.to_legacy_input(envelope)
        assert legacy == "Hello"
    
    def test_round_trip(self):
        original = {"test": [1, 2, 3]}
        envelopes = EnvelopeAdapter.from_legacy_output(original, "node", "trace")
        converted = EnvelopeAdapter.to_legacy_input(envelopes[0])
        assert converted == original
```

#### 5.2 Integration test with actual handlers

```python
# In /dipeo/tests/refactoring/test_envelope_integration.py

import pytest
from dipeo.application.execution.typed_engine import TypedExecutionEngine
from dipeo.application.execution.typed_execution_context import TypedExecutionContext
from dipeo.domain.diagram.models import ExecutableDiagram
from dipeo.core.execution.envelope import EnvelopeFactory

@pytest.mark.asyncio
async def test_engine_with_envelopes():
    """Test engine executes with envelope support"""
    
    # Create test diagram
    diagram = create_test_diagram_with_code_nodes()
    
    # Create context
    context = TypedExecutionContext(
        execution_id="test-123",
        diagram_id="diagram-1"
    )
    
    # Create engine
    engine = TypedExecutionEngine()
    
    # Execute
    await engine.execute(diagram, context)
    
    # Check outputs are envelopes
    for node in diagram.nodes:
        output = context.get_output(node.id)
        if output:
            # Should be able to get as envelope
            if isinstance(output, Envelope):
                assert output.produced_by == node.id
            else:
                # Legacy output should be convertible
                from dipeo.application.execution.envelope_adapter import EnvelopeAdapter
                envelopes = EnvelopeAdapter.from_legacy_output(output, node.id, "")
                assert len(envelopes) > 0
```

### Step 6: Documentation (Day 11)

#### 6.1 Create `/dipeo/docs/envelope_guide.md`

```markdown
# Envelope System Guide

## Overview

The Envelope system provides standardized message passing between nodes in DiPeO diagrams.

## Core Concepts

### Envelope
An immutable message container with:
- **Identity**: Unique ID and trace ID for tracking
- **Content**: Type-tagged body with optional schema
- **Metadata**: Timestamp, iteration, branch, and custom data

### Content Types
- `raw_text`: Plain text strings
- `object`: JSON-serializable data structures
- `conversation_state`: Conversation memory snapshots
- `binary`: Raw bytes

## Usage in Handlers

### Reading Inputs

```python
class MyHandler(TypedNodeHandler):
    def __init__(self):
        self.reader = EnvelopeReader()
    
    async def execute_request(self, request):
        inputs = await self._resolve_inputs(request)
        
        # Get text input
        text = self.reader.as_text(inputs['prompt'])
        
        # Get structured data
        config = self.reader.as_json(inputs['config'])
        
        # Get with validation
        from pydantic import BaseModel
        class Config(BaseModel):
            timeout: int
            retries: int
        
        validated = self.reader.as_json(inputs['config'], Config)
```

### Creating Outputs

```python
# Text output
return NodeOutput.success().with_envelopes([
    EnvelopeFactory.text("Result text")
])

# JSON output
return NodeOutput.success().with_envelopes([
    EnvelopeFactory.json({"status": "complete", "count": 42})
])

# Multiple outputs
return NodeOutput.success().with_envelopes([
    EnvelopeFactory.text("Summary"),
    EnvelopeFactory.json({"details": {...}})
])
```

## Migration Guide

### Phase 1: Compatibility Mode (Current)
- All existing handlers work unchanged
- Outputs automatically wrapped in envelopes
- Inputs converted from envelopes when needed

### Phase 2: Opt-in Envelopes
- Add `_expects_envelopes = True` to handler class
- Handler receives envelope objects directly
- Better type safety and validation

### Phase 3: Mandatory Envelopes
- All handlers must use envelope interface
- Direct context access deprecated
- Full type safety enforced

## Best Practices

1. **Always use EnvelopeReader** for input extraction
2. **Tag envelopes** with iteration/branch for loops
3. **Include metadata** for debugging and tracing
4. **Validate schemas** when expecting structured data
5. **Handle missing inputs** gracefully

## Troubleshooting

### Common Issues

**Issue**: Cannot extract JSON from text envelope
**Solution**: Use `as_text()` first, then parse manually

**Issue**: Schema validation fails
**Solution**: Check schema matches actual data structure

**Issue**: Missing envelope in inputs
**Solution**: Check edge connections in diagram
```

### Step 7: Rollout Plan (Day 12-14)

#### 7.1 Feature Flag Configuration

```python
# In /dipeo/config/features.py

class FeatureFlags:
    # Envelope system
    ENVELOPE_SYSTEM_ENABLED = True
    ENVELOPE_VALIDATION_STRICT = False
    ENVELOPE_REQUIRE_SCHEMAS = False
    
    # Migration helpers
    ENVELOPE_ADAPTER_WARNINGS = True
    ENVELOPE_LEGACY_SUPPORT = True
```

#### 7.2 Gradual Handler Migration

```python
# Migration order (lowest risk first):
MIGRATION_PHASES = {
    "phase1": [
        "HelloWorldHandler",     # Simplest
        "CommentHandler",        # Text only
        "VariableGetHandler",    # Read only
    ],
    "phase2": [
        "CodeJobHandler",        # Complex but isolated
        "TemplateJobHandler",    # Template processing
        "ApiJobHandler",         # External calls
    ],
    "phase3": [
        "PersonJobHandler",      # Critical path
        "SubDiagramHandler",     # Complex flow
        "ConditionHandler",      # Branch logic
    ]
}
```

## Verification Checklist

### Unit Tests
- [ ] Envelope creation and immutability
- [ ] EnvelopeReader all content types
- [ ] EnvelopeAdapter legacy conversion
- [ ] NodeOutput envelope methods
- [ ] Schema validation

### Integration Tests
- [ ] Engine executes with envelopes
- [ ] Handler receives correct inputs
- [ ] Legacy handlers still work
- [ ] Event emission includes envelopes

### Performance Tests
- [ ] Envelope creation overhead < 0.1ms
- [ ] Memory usage increase < 5%
- [ ] No regression in execution speed

### Documentation
- [ ] API documentation complete
- [ ] Migration guide published
- [ ] Examples updated
- [ ] README reflects changes

## Success Criteria

1. **Zero Breaking Changes**: All existing diagrams execute unchanged
2. **Performance Neutral**: No measurable performance degradation
3. **Type Safety**: 100% of inter-node communication typed
4. **Observability**: All messages traceable via envelope IDs

## Next Phase Trigger

Phase 2 (Handler Interface Enforcement) begins when:
- [ ] All Phase 1 code merged and deployed
- [ ] No critical bugs for 1 week
- [ ] 3+ handlers successfully migrated
- [ ] Performance metrics stable

## Emergency Rollback

If critical issues arise:

1. Set `ENVELOPE_SYSTEM_ENABLED = False`
2. Revert handler changes via feature branch
3. Clear envelope-related caches
4. Monitor for legacy path stability

The system is designed to fall back gracefully to legacy behavior at multiple levels.