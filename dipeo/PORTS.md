# DiPeO Ports Developer Guide

This guide explains how to work with ports in DiPeO's hexagonal architecture, including when to create new ports, how to implement them, and best practices for type safety.

## Table of Contents
1. [Understanding Ports](#understanding-ports)
2. [When to Create a Port](#when-to-create-a-port)
3. [Creating a New Port](#creating-a-new-port)
4. [TYPE_CHECKING Pattern](#type_checking-pattern)
5. [Implementing Adapters](#implementing-adapters)
6. [Testing with Ports](#testing-with-ports)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

## Understanding Ports

Ports are interfaces that define contracts between the core/domain layers and the infrastructure layer. They enable:
- **Dependency Inversion**: Core depends on abstractions, not implementations
- **Testability**: Easy to mock for unit tests
- **Flexibility**: Swap implementations without changing business logic
- **Clear Boundaries**: Explicit contracts between layers

### Port Location
All ports are located in: `dipeo/core/ports/`

### Available Ports
- `ExecutionContextPort` - Execution context and variables
- `StateStorePort` - Execution state persistence
- `MessageRouterPort` - Inter-node messaging
- `FileServicePort` - File system operations
- `LLMServicePort` - LLM provider abstraction
- `NotionServicePort` - Notion API integration

## When to Create a Port

Create a new port when:
1. **External System Integration**: Connecting to a new external service
2. **Infrastructure Abstraction**: Abstracting infrastructure concerns
3. **Multiple Implementations**: You need different implementations for different environments
4. **Testing Requirements**: You need to mock complex external dependencies

Don't create a port for:
- Pure business logic (belongs in domain services)
- Simple data transformations
- Internal domain operations

## Creating a New Port

### Step 1: Define the Protocol

Create a new file in `dipeo/core/ports/`:

```python
# dipeo/core/ports/analytics_service.py
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from dipeo.models import ExecutionID, NodeID, MetricData

@runtime_checkable
class AnalyticsServicePort(Protocol):
    """Port for analytics and metrics collection."""
    
    async def track_execution(
        self, 
        execution_id: "ExecutionID",
        event_name: str,
        properties: dict[str, Any]
    ) -> None:
        """Track an execution event."""
        ...
    
    async def record_metric(
        self,
        node_id: "NodeID",
        metric_data: "MetricData"
    ) -> None:
        """Record performance metrics for a node."""
        ...
```

### Step 2: Export from __init__.py

Add to `dipeo/core/ports/__init__.py`:

```python
from .analytics_service import AnalyticsServicePort

__all__ = [
    # ... existing exports
    "AnalyticsServicePort",
]
```

### Step 3: Use in Domain Service

```python
# dipeo/domain/services/execution/tracking_service.py
from typing import TYPE_CHECKING
from dipeo.core.ports import AnalyticsServicePort

if TYPE_CHECKING:
    from dipeo.models import ExecutionID

class ExecutionTrackingService:
    def __init__(self, analytics: AnalyticsServicePort):
        self._analytics = analytics
    
    async def track_start(self, execution_id: "ExecutionID") -> None:
        await self._analytics.track_execution(
            execution_id,
            "execution_started",
            {"timestamp": datetime.now().isoformat()}
        )
```

## TYPE_CHECKING Pattern

The TYPE_CHECKING pattern prevents circular dependencies while maintaining type safety:

### Why Use TYPE_CHECKING?

1. **Prevents Circular Imports**: Domain types aren't imported at runtime
2. **Maintains Type Safety**: Full IDE support and type checking
3. **Clean Architecture**: Enforces dependency rules

### Pattern Template

```python
from typing import TYPE_CHECKING, Protocol, runtime_checkable

# Import domain types only for type checking
if TYPE_CHECKING:
    from dipeo.models import (
        DomainType1,
        DomainType2,
    )

@runtime_checkable
class YourPort(Protocol):
    # Use string annotations for domain types
    async def method(self, param: "DomainType1") -> "DomainType2":
        ...
```

### Important Notes

1. **Always use string annotations** for imported types: `"DomainType"`
2. **Import all domain types** in the TYPE_CHECKING block
3. **Never import domain types** outside TYPE_CHECKING
4. **Use runtime_checkable** if you need isinstance() checks

## Implementing Adapters

Adapters are concrete implementations of ports, located in `dipeo/infra/`:

### Example Implementation

```python
# dipeo/infra/analytics/mixpanel_adapter.py
from dipeo.core.ports import AnalyticsServicePort
from dipeo.models import ExecutionID, NodeID, MetricData
import mixpanel

class MixpanelAdapter:
    """Mixpanel implementation of AnalyticsServicePort."""
    
    def __init__(self, token: str):
        self._mp = mixpanel.Mixpanel(token)
    
    async def track_execution(
        self, 
        execution_id: ExecutionID,
        event_name: str,
        properties: dict[str, Any]
    ) -> None:
        # Note: No string annotations needed in implementation
        self._mp.track(str(execution_id), event_name, properties)
    
    async def record_metric(
        self,
        node_id: NodeID,
        metric_data: MetricData
    ) -> None:
        self._mp.track(str(node_id), "metric_recorded", {
            "value": metric_data.value,
            "unit": metric_data.unit,
        })
```

### Registration in Container

```python
# dipeo/container/container.py
from dipeo.infra.analytics import MixpanelAdapter

class Container:
    def __init__(self):
        # ... existing setup
        self._analytics = MixpanelAdapter(config.MIXPANEL_TOKEN)
    
    @property
    def analytics(self) -> AnalyticsServicePort:
        return self._analytics
```

## Testing with Ports

Ports make testing easy through mocking:

### Unit Test Example

```python
# tests/domain/services/test_tracking_service.py
from unittest.mock import AsyncMock
import pytest
from dipeo.domain.services.execution import ExecutionTrackingService
from dipeo.models import ExecutionID

@pytest.fixture
def mock_analytics():
    """Create a mock analytics port."""
    mock = AsyncMock()
    mock.track_execution = AsyncMock()
    return mock

async def test_track_start(mock_analytics):
    service = ExecutionTrackingService(mock_analytics)
    execution_id = ExecutionID("test-123")
    
    await service.track_start(execution_id)
    
    mock_analytics.track_execution.assert_called_once_with(
        execution_id,
        "execution_started",
        mock.ANY  # Don't care about exact timestamp
    )
```

### Integration Test Example

```python
# tests/integration/test_analytics_integration.py
from dipeo.infra.analytics import InMemoryAnalytics

async def test_full_execution_tracking():
    # Use in-memory implementation for testing
    analytics = InMemoryAnalytics()
    service = ExecutionTrackingService(analytics)
    
    await service.track_start(execution_id)
    
    # Verify through the in-memory store
    events = analytics.get_events(execution_id)
    assert len(events) == 1
    assert events[0]["name"] == "execution_started"
```

## Common Patterns

### 1. Optional Ports

Some ports might be optional:

```python
class MyService:
    def __init__(self, analytics: AnalyticsServicePort | None = None):
        self._analytics = analytics
    
    async def do_work(self):
        # ... do the work
        
        if self._analytics:
            await self._analytics.track_execution(...)
```

### 2. Port Composition

Combine multiple ports in a service:

```python
class ExecutionService:
    def __init__(
        self,
        state_store: StateStorePort,
        message_router: MessageRouterPort,
        analytics: AnalyticsServicePort,
    ):
        self._state = state_store
        self._router = message_router
        self._analytics = analytics
```

### 3. Port Factories

For dynamic port selection:

```python
from typing import Protocol

class PortFactory(Protocol):
    def create_llm_service(self, provider: str) -> LLMServicePort:
        ...
```

## Troubleshooting

### Common Issues

1. **Circular Import Error**
   - **Symptom**: ImportError at runtime
   - **Solution**: Ensure domain types are only imported in TYPE_CHECKING block

2. **Type Checker Errors**
   - **Symptom**: Mypy/pyright complains about string annotations
   - **Solution**: Make sure types are imported in TYPE_CHECKING block

3. **Runtime Type Errors**
   - **Symptom**: AttributeError when using port
   - **Solution**: Ensure adapter properly implements all protocol methods

4. **Missing Quotes**
   - **Symptom**: NameError for domain types
   - **Solution**: Use string annotations: `"DomainType"` not `DomainType`

### Debug Checklist

- [ ] All domain type imports are in TYPE_CHECKING block
- [ ] All domain type annotations use quotes
- [ ] Port is exported from `__init__.py`
- [ ] Adapter implements all required methods
- [ ] Container properly instantiates and exposes adapter
- [ ] No direct imports between layers (only through ports)

## Best Practices Summary

1. **Keep Ports Minimal**: Only include what's needed by core/domain
2. **Use TYPE_CHECKING**: Always for domain type imports
3. **Document Thoroughly**: Ports are contracts - document them well
4. **Single Responsibility**: Each port should have one clear purpose
5. **Async First**: Make methods async even if implementation is sync
6. **Error Handling**: Define clear error types in port documentation
7. **Version Carefully**: Changing ports affects all implementations