# GraphQL Subscriptions Implementation Guide

## Overview

DiPeO uses GraphQL subscriptions exclusively for real-time updates. The previous SSE (Server-Sent Events) and WebSocket implementations have been removed. GraphQL subscriptions handle all real-time communication through a unified transport mechanism. This guide explains how to add new subscriptions and maintain the subscription system.

## Architecture

### Components

1. **Backend Subscription Handler** (`/dipeo/application/graphql/schema/subscriptions.py`)
   - Defines GraphQL subscription endpoints
   - Connects to MessageRouter for event distribution
   - Serializes data for JSON compatibility

2. **Event System** (`/dipeo/diagram_generated/enums.py`)
   - EventType enum defines all available event types
   - Events are emitted by observers and handlers

3. **Message Router** (`/dipeo/infrastructure/adapters/messaging/`)
   - Broadcasts events to all connected subscribers
   - Manages connection lifecycle
   - Buffers events for late subscribers

4. **Frontend Hooks** (`/apps/web/src/domain/execution/hooks/`)
   - React hooks that subscribe to GraphQL subscriptions
   - Process incoming events and update UI state

## Adding a New Subscription

### Step 1: Define Event Type

Add new event type to TypeScript enum:
```typescript
// /dipeo/models/src/core/enums/execution.ts
export enum EventType {
  // ... existing events
  YOUR_NEW_EVENT = 'YOUR_NEW_EVENT'
}
```

Regenerate backend models:
```bash
cd /dipeo/models && pnpm build
dipeo run codegen/diagrams/generate_all --light --debug
make apply-syntax-only
```

### Step 2: Create GraphQL Subscription

Add subscription to backend schema:
```python
# /dipeo/application/graphql/schema/subscriptions.py
@strawberry.subscription
async def your_new_subscription(
    self, execution_id: strawberry.ID
) -> AsyncGenerator[JSONScalar, None]:
    """Subscribe to your new events."""
    message_router = registry.get(MESSAGE_ROUTER)
    
    if not message_router:
        logger.error("Message router not available")
        return
    
    exec_id = ExecutionID(str(execution_id))
    
    try:
        # Create event queue
        event_queue = asyncio.Queue()
        connection_id = f"graphql-your-subscription-{id(event_queue)}"
        
        # Define handler
        async def event_handler(message):
            serialized_message = serialize_for_json(message)
            await event_queue.put(serialized_message)
        
        # Register and subscribe
        await message_router.register_connection(connection_id, event_handler)
        await message_router.subscribe_connection_to_execution(connection_id, str(exec_id))
        
        try:
            # Yield events
            while True:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                    # Filter for your event type
                    if event.get("type") == EventType.YOUR_NEW_EVENT.value:
                        yield serialize_for_json(event.get("data", {}))
                except asyncio.TimeoutError:
                    continue
        finally:
            # Clean up
            await message_router.unsubscribe_connection_from_execution(connection_id, str(exec_id))
            await message_router.unregister_connection(connection_id)
            
    except Exception as e:
        logger.error(f"Error in subscription: {e}")
        raise
```

### Step 3: Update Frontend Query Generator

Add subscription to query generator:
```python
# /files/codegen/code/frontend/queries/executions_queries.py
# In generate() method, add:
queries.append("""subscription YourNewSubscription($executionId: ID!) {
  your_new_subscription(execution_id: $executionId)
}""")
```

Regenerate frontend queries:
```bash
dipeo run codegen/diagrams/generate_all --light --debug
make apply-syntax-only
make graphql-schema
```

### Step 4: Create Frontend Hook

Create React hook for the subscription:
```typescript
// /apps/web/src/domain/execution/hooks/useYourNewSubscription.ts
import { useState, useEffect } from 'react';
import { executionId } from '@/infrastructure/types';
import { useYourNewSubscriptionSubscription } from '@/__generated__/graphql';

export function useYourNewSubscription(executionIdParam: ReturnType<typeof executionId> | null) {
  const [data, setData] = useState<YourDataType[]>([]);

  const { data: subscriptionData } = useYourNewSubscriptionSubscription({
    variables: { executionId: executionIdParam || '' },
    skip: !executionIdParam,
  });

  useEffect(() => {
    if (subscriptionData?.your_new_subscription) {
      // Process incoming data
      const newData = subscriptionData.your_new_subscription;
      setData(prev => [...prev, newData]);
    }
  }, [subscriptionData]);

  return { data };
}
```

### Step 5: Emit Events

Emit events from observers or handlers:
```python
# In any observer or handler
await self.message_router.broadcast_to_execution(
    execution_id,
    {
        "type": EventType.YOUR_NEW_EVENT.value,
        "execution_id": execution_id,
        "data": {
            # Your event data
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
)
```

## Example: ExecutionLogs Implementation

The ExecutionLogs subscription was implemented following these steps:

1. **Event Type**: Added `EXECUTION_LOG` to EventType enum
2. **GraphQL Subscription**: Created `execution_logs` subscription
3. **Frontend Query**: Added to executions_queries.py generator
4. **React Hook**: Created `useExecutionLogStream` hook
5. **Event Emission**: UnifiedEventObserver emits EXECUTION_LOG events

## Best Practices

1. **Event Naming**: Use UPPER_SNAKE_CASE for event types
2. **Data Serialization**: Always use `serialize_for_json()` for complex objects
3. **Error Handling**: Include try-catch blocks and cleanup in finally
4. **Timeout Handling**: Use `asyncio.wait_for` with appropriate timeouts
5. **Connection Cleanup**: Always unsubscribe and unregister on completion

## Testing Subscriptions

### Backend Testing
```python
# Test event emission
await message_router.broadcast_to_execution(exec_id, test_event)

# Verify subscription receives event
# Check logs for connection registration
```

### Frontend Testing
```bash
# Run dev server with debug mode
pnpm dev

# Open browser DevTools
# Check Network tab for WebSocket connections
# Monitor GraphQL subscription messages
```

### CLI Testing
```bash
# Run diagram with debug flag
dipeo run [diagram] --debug

# Check logs for event emissions
# Monitor execution in web UI at http://localhost:3000/?monitor=true
```

## Common Issues

### Issue: Events not received
- Check MessageRouter connection registration
- Verify event type matches filter
- Ensure execution_id is correct

### Issue: Duplicate events
- Check for multiple subscriptions
- Verify cleanup is working properly
- Look for event being emitted multiple times

### Issue: Memory leaks
- Ensure proper cleanup in finally blocks
- Check for unclosed connections
- Monitor queue sizes

## Migration from SSE/WebSocket

The system migrated from SSE and WebSocket to GraphQL subscriptions for:
- Unified transport mechanism (single protocol for all real-time updates)
- Better type safety with generated types
- Improved error handling and reconnection logic
- Simplified client code (no need for multiple transport implementations)
- Reduced complexity in the infrastructure layer

All SSE endpoints and direct WebSocket connections have been removed and replaced with GraphQL subscriptions. The system now uses only GraphQL's built-in WebSocket transport for subscriptions.

## Related Documentation

- [DiPeO Application Layer](../dipeo/application/CLAUDE.md)
- [Infrastructure Events](../dipeo/infrastructure/events/CLAUDE.md)
- [Frontend Architecture](../apps/web/CLAUDE.md)
- [Code Generation](../files/codegen/CLAUDE.md)