// Execution types
import { Node, NodeType } from './node';
import { Arrow } from './arrow';
import { Diagram } from './diagram';

export interface ExecutionContext {
  execution_id: string;
  node_outputs: Record<string, unknown>;
  node_execution_counts: Record<string, number>;
  total_cost: number;
  start_time: number;
  errors: Record<string, string>;
  execution_order: string[];
  condition_values: Record<string, boolean>;
  first_only_consumed: Record<string, boolean>;
  diagram?: Diagram | null;
  // Frontend aliases (snake_case) 
  nodes_by_id: Record<string, Node>;
  outgoing_arrows: Record<string, Arrow[]>;
  incoming_arrows: Record<string, Arrow[]>;
}

export interface ExecutionMetadata {
  execution_id: string;
  start_time: number;
  end_time?: number;
  total_cost: number;
  node_count: number;
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
  finalOutputs: Record<string, unknown>;
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
  node_id?: string;
  node_type?: NodeType;
  message: string;
  details?: Record<string, unknown>;
  timestamp: Date;
  stack?: string;
}