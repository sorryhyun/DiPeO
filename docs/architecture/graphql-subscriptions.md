# GraphQL Subscriptions Implementation Guide

## Overview

DiPeO uses GraphQL subscriptions exclusively for real-time updates. GraphQL subscriptions handle all real-time communication through a unified WebSocket transport mechanism. This guide explains the subscription system architecture and how to add new subscriptions.

### Available Subscriptions

1. **execution_updates**: Main subscription for execution lifecycle events
   - Handles all execution-related events (start, complete, fail, logs, etc.)
   - Used by frontend monitoring and logging components

2. **node_updates**: Node-specific status updates
   - Tracks individual node state changes and progress
   - Optional filtering by node_id

3. **interactive_prompts**: User interaction requests
   - Handles prompts requiring user input during execution
   - Used by UserResponseNode and interactive workflows

4. **execution_logs**: Dedicated log streaming
   - Filters specifically for EXECUTION_LOG events
   - Used by log viewing components

## Architecture

### Components

1. **Backend Subscription Handler** (`/dipeo/application/graphql/schema/subscriptions.py`)
   - Defines GraphQL subscription endpoints
   - Connects to MessageRouter for event distribution
   - Serializes data for JSON compatibility
   - Currently implements 4 subscriptions: `execution_updates`, `node_updates`, `interactive_prompts`, `execution_logs`

2. **Event System** (`/dipeo/diagram_generated/enums.py`)
   - EventType enum defines all available event types
   - Events are emitted through the AsyncEventBus
   - Events include: `EXECUTION_STARTED`, `NODE_COMPLETED`, `NODE_STATUS_CHANGED`, `EXECUTION_LOG`, etc.

3. **Message Router** (`/dipeo/infrastructure/adapters/messaging/message_router.py`)
   - Central message distribution hub
   - Manages connection lifecycle
   - Features:
     - Event buffering (last 50 events per execution, 5-minute TTL)
     - Event batching for performance (configurable interval and size)
     - Connection health monitoring
     - Backpressure handling with bounded queues

4. **Frontend Hooks** (`/apps/web/src/domain/execution/hooks/`)
   - React hooks that subscribe to GraphQL subscriptions
   - Process incoming events and update UI state
   - Example: `useExecutionLogStream` for log streaming

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

### Step 3: Add Subscription to Query Definitions

Add subscription to the appropriate query definition file:
```typescript
// /dipeo/models/src/frontend/query-definitions/executions.ts
// Add to executionQueries.queries array:
{
  name: 'YourNewSubscription',
  type: QueryOperationType.SUBSCRIPTION,
  variables: [
    { name: 'execution_id', type: 'ID', required: true }
  ],
  fields: [
    {
      name: 'your_new_subscription',
      args: [
        { name: 'execution_id', value: 'execution_id', isVariable: true }
      ],
      fields: [
        { name: 'field1' },
        { name: 'field2' },
        // ... subscription fields
      ]
    }
  ]
}
```

Regenerate frontend queries:
```bash
# Build TypeScript models
cd dipeo/models && pnpm build

# Run code generation
dipeo run codegen/diagrams/generate_all --light --debug
make apply-syntax-only

# Update GraphQL schema and TypeScript types
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

Emit events using the AsyncEventBus:
```python
# In any handler or service
from dipeo.core.events import AsyncEventBus, Event

event_bus = AsyncEventBus.get_instance()
await event_bus.emit(Event(
    type=EventType.YOUR_NEW_EVENT,
    execution_id=execution_id,
    data={
        # Your event data
    }
))
```

The MessageRouter automatically picks up these events and distributes them to subscribed connections.

## Example: ExecutionUpdates Implementation

The ExecutionUpdates subscription demonstrates the complete implementation pattern:

1. **Event Types**: Multiple event types are handled - `EXECUTION_STARTED`, `NODE_COMPLETED`, `EXECUTION_LOG`, etc.
2. **GraphQL Subscription**: `execution_updates` in `/dipeo/application/graphql/schema/subscriptions.py`
3. **Frontend Query Definition**: Defined in `/dipeo/models/src/frontend/query-definitions/executions.ts`
4. **Generated Query**: Created in `/apps/web/src/__generated__/queries/all-queries.ts`
5. **React Hook**: `useExecutionLogStream` uses `useExecutionUpdatesSubscription` 
6. **Event Emission**: AsyncEventBus emits events that MessageRouter distributes

## Best Practices

1. **Event Naming**: Use UPPER_SNAKE_CASE for event types
2. **Data Serialization**: Always use `serialize_for_json()` for complex objects
3. **Error Handling**: Include try-catch blocks and cleanup in finally
4. **Timeout Handling**: Use `asyncio.wait_for` with appropriate timeouts
5. **Connection Cleanup**: Always unsubscribe and unregister on completion

## Testing Subscriptions

### Backend Testing
```python
# Test event emission via AsyncEventBus
from dipeo.infrastructure.events.adapters.legacy import AsyncEventBus, Event
from dipeo.diagram_generated.enums import EventType

event_bus = AsyncEventBus.get_instance()
await event_bus.emit(Event(
    type=EventType.EXECUTION_LOG,
    execution_id="test-exec-id",
    data={"message": "Test log", "level": "INFO"}
))

# Verify in logs that MessageRouter distributes the event
```

### Frontend Testing
```bash
# Run dev server with GraphQL playground
make dev-all

# Open GraphQL playground at http://localhost:8000/graphql
# Test subscription directly:
subscription {
  execution_updates(execution_id: "your-exec-id") {
    execution_id
    event_type
    data
    timestamp
  }
}

# Monitor WebSocket frames in browser DevTools Network tab
```

### CLI Testing
```bash
# Run diagram with debug flag
dipeo run [diagram] --debug

# Monitor execution in web UI
# Open http://localhost:3000/?monitor=true
# Check console logs for subscription events
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

## Architecture Notes

### Current Implementation
The system uses GraphQL subscriptions exclusively for real-time updates:
- **Transport**: GraphQL WebSocket transport via Apollo Client
- **Backend**: Strawberry GraphQL with async generators
- **Message Router**: Central hub for event distribution with batching and buffering
- **Type Safety**: Generated TypeScript types from GraphQL schema

### Multi-Worker Support
For production deployments with multiple workers:
- Redis is required for GraphQL subscriptions to work across workers
- Without Redis, subscriptions only work with single worker deployments
- Configuration: Set `REDIS_URL` environment variable for multi-worker support

### Event System Integration
- Events are emitted via `AsyncEventBus` 
- `MessageRouter` subscribes to events and distributes to GraphQL connections
- Event batching improves performance for high-frequency updates
- Bounded queues prevent memory issues with backpressure handling

## Related Documentation

- [DiPeO Application Layer](../../dipeo/application/CLAUDE.md) - GraphQL schema and resolver implementation
- [Infrastructure Layer](../../dipeo/infrastructure/CLAUDE.md) - MessageRouter and event system details
- [Frontend Architecture](../../apps/web/CLAUDE.md) - Frontend subscription hooks and state management
- [Code Generation](../../projects/codegen/CLAUDE.md) - How queries and subscriptions are generated
- [DiPeO Models](../../dipeo/models/CLAUDE.md) - TypeScript query definitions source