# Unified Real-Time Monitoring Migration Guide

## Overview

This guide describes the migration from the current dual-observer monitoring system to a unified architecture using `MessageRouter` as the central event bus.

## Current Architecture (Before Migration)

```
CLI Executions:
  execute_diagram() → MonitoringStreamObserver → SSE endpoint → Browser

Web Executions:  
  execute_diagram() → EventPublishingObserver → MessageRouter → GraphQL Subscriptions
```

**Problems:**
- Duplicate code and logic between two observers
- Inconsistent event formats
- Harder to maintain and extend
- No single source of truth for monitoring

## Unified Architecture (After Migration)

```
ALL Executions:
  execute_diagram() → UnifiedEventObserver → MessageRouter
                                                    ↓
                            ┌─────────────────────┼─────────────────────┐
                            ↓                     ↓                     ↓
                    SSEMessageRouterAdapter   GraphQL Subs      Future Transports
                            ↓                     ↓
                      CLI Browser            Web Browser
```

**Benefits:**
- Single observer implementation
- MessageRouter as central event bus
- Consistent event format across all clients
- Easy to add new transport mechanisms
- Better testability and maintainability

## Migration Steps

### Phase 1: Add New Components (Non-Breaking)

1. **Deploy new unified components alongside existing ones:**
   ```python
   # New files added:
   /dipeo/infrastructure/adapters/messaging/sse_adapter.py
   /dipeo/application/execution/observers/unified_event_observer.py
   /apps/server/src/dipeo_server/api/sse_unified.py
   ```

2. **Update execute_diagram to support unified mode:**
   ```python
   # In execute_diagram.py
   if use_unified_monitoring:  # New flag
       observer = UnifiedEventObserver(message_router, typed_diagram)
       engine_observers = [observer]
   else:
       # Keep existing logic for backward compatibility
       ...
   ```

3. **Add unified SSE endpoint:**
   ```python
   # In main.py server setup
   from dipeo_server.api import sse_unified
   app.include_router(sse_unified.router)  # Available at /sse/unified/
   ```

### Phase 2: Test in Parallel

1. **Update CLI to optionally use unified endpoint:**
   ```python
   # Add --unified flag to dipeo run command
   dipeo run diagram --unified  # Uses new unified monitoring
   dipeo run diagram            # Uses existing monitoring
   ```

2. **Test both paths thoroughly:**
   - CLI with unified monitoring
   - Web with unified monitoring
   - Verify event consistency
   - Check performance metrics

### Phase 3: Gradual Migration

1. **Update CLI to use unified by default:**
   ```python
   # Make unified the default, add --legacy flag for old behavior
   use_unified = not args.legacy
   ```

2. **Monitor for issues:**
   - Track error rates
   - Compare event latency
   - Gather user feedback

### Phase 4: Complete Migration

1. **Remove old components:**
   ```python
   # Delete after confirming stability:
   /dipeo/application/execution/observers/monitoring_stream_observer.py
   /dipeo/application/execution/observers/event_publishing_observer.py
   /apps/server/src/dipeo_server/api/sse.py (old SSE endpoint)
   ```

2. **Simplify execute_diagram:**
   ```python
   # Remove branching logic, always use UnifiedEventObserver
   observer = UnifiedEventObserver(message_router, typed_diagram)
   ```

3. **Update documentation**

## Code Examples

### Using UnifiedEventObserver

```python
from dipeo.application.execution.observers import UnifiedEventObserver
from dipeo.application.registry import MESSAGE_ROUTER

# In execute_diagram use case
message_router = registry.resolve(MESSAGE_ROUTER)
observer = UnifiedEventObserver(
    message_router=message_router,
    execution_runtime=typed_diagram,
    capture_logs=True  # Enable log capture for CLI
)

engine = TypedExecutionEngine(observers=[observer])
```

### Consuming Events via SSE

```python
# Client-side JavaScript
const eventSource = new EventSource('/sse/executions/exec-123');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch(data.type) {
        case 'NODE_STATUS_CHANGED':
            updateNodeStatus(data.data);
            break;
        case 'EXECUTION_LOG':
            appendLog(data.data);
            break;
    }
};
```

### Adding New Transport Mechanisms

```python
# Easy to add new transports by subscribing to MessageRouter
class WebhookAdapter:
    def __init__(self, message_router: MessageRouterPort):
        self.message_router = message_router
    
    async def forward_to_webhook(self, execution_id: str, webhook_url: str):
        connection_id = f"webhook-{execution_id}"
        
        async def webhook_handler(message: dict):
            async with aiohttp.ClientSession() as session:
                await session.post(webhook_url, json=message)
        
        await self.message_router.register_connection(connection_id, webhook_handler)
        await self.message_router.subscribe_connection_to_execution(
            connection_id, execution_id
        )
```

## Testing Checklist

- [ ] CLI executions with unified monitoring
- [ ] Web executions remain unchanged
- [ ] SSE streaming performance
- [ ] Log capture functionality
- [ ] Sub-diagram event propagation
- [ ] Error handling and recovery
- [ ] Connection cleanup on completion
- [ ] Concurrent execution monitoring
- [ ] Memory usage under load

## Rollback Plan

If issues arise during migration:

1. **Immediate rollback:** Set `use_unified_monitoring=False` flag
2. **Keep both systems:** Run in parallel until issues resolved
3. **Gradual fix:** Address issues while old system remains active

## Performance Considerations

- **Queue sizes:** SSEMessageRouterAdapter uses bounded queues (max 100 events)
- **Backpressure:** Events dropped if client can't keep up
- **Heartbeats:** 10-second intervals to maintain SSE connections
- **Cleanup:** Automatic connection cleanup on execution completion

## Future Enhancements

With MessageRouter as the central event bus, we can easily add:

1. **WebRTC data channels** for peer-to-peer monitoring
2. **Webhook notifications** for external integrations
3. **Event persistence** for replay functionality
4. **Event filtering** by type or node
5. **Multi-execution dashboards** with aggregated events
6. **Distributed tracing** integration