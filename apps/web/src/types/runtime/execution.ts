import type { Dict } from '../primitives';
import type { NodeID, ExecutionID } from '../branded';

export interface ExecutionOptions {
  mode?: 'monitor' | 'headless' | 'check';
  debug?: boolean;
  delay?: number;
  continueOnError?: boolean;
  allowPartial?: boolean;
  debugMode?: boolean;
}

export interface ExecutionState<C = Dict> {
  id: ExecutionID;
  running: NodeID[];
  completed: NodeID[];
  skipped: NodeID[];
  paused: NodeID[];
  context: C;
  errors: Dict<string>;
  isRunning: boolean;
  startedAt?: string;
  endedAt?: string;
  totalTokens?: number;
}

export interface ExecutionUpdate {
  type: string;
  executionId?: ExecutionID;
  node_id?: string;
  progress?: string;
  output?: unknown;
  output_preview?: string;
  error?: string;
  status?: string;
  total_nodes?: number;
  context?: Dict;
  duration?: number;
  nodeType?: string;
  nodeId?: NodeID;
  message?: string;
  details?: Dict;
  totalTokens?: number;
  tokens?: number;
  timestamp?: string;
  conversationId?: string;
}

export interface ExecutionResult {
  success?: boolean;
  executionId?: ExecutionID;
  context?: Record<string, unknown>;
  totalTokens?: number;
  duration?: number;
  finalContext?: Record<string, unknown>;
  error?: string;
  metadata?: {
    totalTokens?: number;
    executionTime?: number;
  };
}