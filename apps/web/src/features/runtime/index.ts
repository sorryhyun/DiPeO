// Unified Backend Execution
// All execution logic is handled by the backend unified engine.
// Frontend uses a simple API client for execution.

export * from './websocket-execution-client';
export * from './hooks/useDiagramRunner';

// WebSocket support for real-time bidirectional communication
export * from './websocket-client';
export * from './hooks/useWebSocket';
export * from './hooks/useWebSocketMonitor';
export * from './components/WebSocketTest';