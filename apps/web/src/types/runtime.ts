// Runtime types - Execution, WebSocket, and real-time state

export interface ExecutionState {
  executionId: string;
  isRunning: boolean;
  runningNodes: string[];
  completedNodes: string[];
  skippedNodes: string[];
  pausedNodes: string[];
  context: Record<string, any>;
  errors: Record<string, string>;
  totalCost?: number;
  startTime?: string;
  endTime?: string;
}

export interface ExecutionOptions {
  mode?: 'monitor' | 'headless' | 'check';
  debug?: boolean;
  delay?: number;
}

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

// Alias for backward compatibility
export type WSMessage = WebSocketMessage;

export interface MessageHandler {
  (message: WSMessage): void;
}

export interface WebSocketClientOptions {
  url?: string;
  debug?: boolean;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  reconnectDecay?: number;
}

export interface NodeExecutionEvent {
  type: 'node_start' | 'node_progress' | 'node_complete' | 'node_error' | 'node_paused' | 'node_resumed' | 'node_skipped';
  nodeId: string;
  nodeType?: string;
  message?: string;
  output?: any;
  error?: string;
  cost?: number;
}

export interface ExecutionControlMessage {
  type: 'pause_node' | 'resume_node' | 'skip_node' | 'abort_execution';
  nodeId?: string;
  executionId?: string;
}

export interface InteractivePrompt {
  nodeId: string;
  prompt: string;
  timeout: number;
  timestamp: string;
}

export interface InteractivePromptData {
  nodeId: string;
  executionId: string;
  prompt: string;
  timeout?: number;
  timeRemaining?: number;
  isOpen?: boolean;
  context?: {
    person_id?: string;
    person_name?: string;
    model?: string;
    service?: string;
    execution_count?: number;
    nodeType?: string;
  };
}

// Execution lifecycle events
export interface ExecutionStartedEvent {
  type: 'execution_started';
  executionId: string;
  total_nodes: number;
}

export interface ExecutionCompleteEvent {
  type: 'execution_complete';
  executionId: string;
  totalCost?: number;
  duration?: number;
}

export interface ExecutionAbortedEvent {
  type: 'execution_aborted';
  executionId: string;
  reason?: string;
}

// Node control types
export interface NodeControlState {
  [nodeId: string]: {
    status: 'running' | 'paused' | 'completed' | 'skipped' | 'error';
    canPause: boolean;
    canResume: boolean;
    canSkip: boolean;
  };
}

// Monitoring types
export interface MonitoringData {
  executionId: string;
  startTime: string;
  currentNode?: string;
  progress: {
    completed: number;
    total: number;
    percentage: number;
  };
  performance: {
    averageNodeTime: number;
    totalCost: number;
    memoryUsage?: number;
  };
}