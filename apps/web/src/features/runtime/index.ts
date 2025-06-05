// Unified Backend Execution
// All execution logic is handled by the backend unified engine.
// Frontend uses a simple API client for execution.

export {
  createWebSocketExecutionClient
} from './websocket-execution-client';
export type {
  DiagramData,
  ExecutionOptions,
  ExecutionUpdate,
  ExecutionResult,
  WebSocketExecutionClient
} from './websocket-execution-client';

export { useDiagramRunner } from './hooks/useDiagramRunner';

// WebSocket support for real-time bidirectional communication
export {
  getWebSocketClient,
  disconnectWebSocketClient
} from './websocket-client';
export type {
  WSMessage,
  MessageHandler,
  ConnectionHandler,
  WebSocketClientOptions,
  WebSocketClient
} from './websocket-client';

export {
  useWebSocket,
  useWebSocketMessage
} from './hooks/useWebSocket';
export type {
  UseWebSocketOptions,
  UseWebSocketReturn
} from './hooks/useWebSocket';

export { useWebSocketMonitor } from './hooks/useWebSocketMonitor';
export { WebSocketTest } from './components/WebSocketTest';