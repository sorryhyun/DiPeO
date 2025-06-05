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