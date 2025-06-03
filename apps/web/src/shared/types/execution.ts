// Execution types
import { Node, NodeType } from './node';
import { Arrow } from './arrow';
import { Diagram } from './diagram';

export interface ExecutionContext {
  executionId: string;
  nodeOutputs: Record<string, unknown>;
  nodeExecutionCounts: Record<string, number>;
  totalCost: number;
  startTime: number;
  errors: Record<string, string>;
  executionOrder: string[];
  conditionValues: Record<string, boolean>;
  firstOnlyConsumed: Record<string, boolean>;
  diagram?: Diagram | null;
  // Frontend aliases (camelCase) 
  nodesById: Record<string, Node>;
  outgoingArrows: Record<string, Arrow[]>;
  incomingArrows: Record<string, Arrow[]>;
}

export interface ExecutionMetadata {
  executionId: string;
  startTime: number;
  endTime?: number;
  totalCost: number;
  nodeCount: number;
  status: ExecutionStatus;
}

export type ExecutionStatus = 
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'paused';

export interface ExecutionResult {
  success: boolean;
  context: ExecutionContext;
  metadata: ExecutionMetadata;
  finalOutputs: Record<string, any>;
  errors: ExecutionError[];
}

export interface ExecutionOptions {
  streaming?: boolean;
  maxIterations?: number;
  timeout?: number;
  skipValidation?: boolean;
  debugMode?: boolean;
}

export interface ExecutionError {
  nodeId?: string;
  nodeType?: NodeType;
  message: string;
  details?: Record<string, any>;
  timestamp: Date;
  stack?: string;
}