# DiPeoWebSocket Usage Guide

The `DiPeoWebSocket` class provides a high-level interface for diagram execution and monitoring with automatic connection management.

## Basic Usage

### Execution Context

```typescript
import { DiPeoWebSocket } from '@/shared/websocket';
import { useDiagramData } from '@/hooks/selectors';

// Get execution instance
const ws = DiPeoWebSocket.forExecution();

// Execute diagram
const diagram = useDiagramData();
const result = await ws.execute(diagram, {
  monitor: true,
  debug: false,
  timeout: 60000
});

// Control execution
await ws.pause();
await ws.resume();
await ws.skipNode(nodeId, 'User requested skip');
await ws.stop();

// Handle prompts
ws.on('prompt:request', ({ nodeId, prompt }) => {
  // Show UI for user input
  const response = await getUserInput(prompt);
  await ws.sendPromptResponse(nodeId, response);
});
```

### Monitoring Context

```typescript
const ws = DiPeoWebSocket.forMonitoring();

// Monitor existing execution
await ws.monitor(executionId);

// Listen to events
ws.on('node:started', ({ nodeId, timestamp }) => {
  console.log(`Node ${nodeId} started`);
});

ws.on('node:completed', ({ nodeId, result }) => {
  console.log(`Node ${nodeId} completed:`, result);
});
```

## Event Types

### Connection Events
- `connected` - WebSocket connected
- `disconnected` - WebSocket disconnected
- `error` - Connection error

### Execution Events
- `execution:started` - Execution began
- `execution:completed` - Execution finished successfully
- `execution:failed` - Execution failed
- `execution:paused` - Execution paused
- `execution:resumed` - Execution resumed

### Node Events
- `node:started` - Node execution started
- `node:completed` - Node execution completed
- `node:failed` - Node execution failed
- `node:skipped` - Node was skipped

### Interactive Events
- `prompt:request` - Node requests user input
- `prompt:response` - User provided input

## React Hook Example

```typescript
function useExecution() {
  const [isExecuting, setIsExecuting] = useState(false);
  const [nodeStates, setNodeStates] = useState<Map<string, NodeExecutionState>>();
  
  useEffect(() => {
    const ws = DiPeoWebSocket.forExecution();
    
    ws.on('execution:started', () => setIsExecuting(true));
    ws.on('execution:completed', () => setIsExecuting(false));
    ws.on('execution:failed', () => setIsExecuting(false));
    
    ws.on('node:started', ({ nodeId }) => {
      setNodeStates(prev => new Map(prev).set(nodeId, {
        status: 'running',
        timestamp: Date.now()
      }));
    });
    
    return () => ws.disconnect();
  }, []);
  
  return { isExecuting, nodeStates };
}
```

## Advanced Features

### Singleton Pattern
- Instances are shared per context type
- `forExecution()` and `forMonitoring()` return the same instance
- Prevents multiple connections for the same purpose

### Automatic Reconnection
- Inherited from underlying WebSocket client
- Exponential backoff for reconnect attempts
- Configurable max attempts and intervals

### Promise-based API
- All async operations return promises
- Built-in timeouts for safety
- Proper error handling with descriptive messages

### Event Emitter Pattern
- Standard Node.js EventEmitter interface
- Type-safe event names
- Multiple listeners per event supported