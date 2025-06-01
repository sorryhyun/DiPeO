// Shared types for both frontend and backend
export interface DiagramNode {
  id: string;
  type: string;
  data: Record<string, any>;
  position?: { x: number; y: number };
}

export interface DiagramArrow {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  data?: Record<string, any>;
  label?: string;
}

export interface Diagram {
  nodes: DiagramNode[];
  arrows: DiagramArrow[];
}

export interface ExecutionContext {
  nodes_by_id: Record<string, DiagramNode>;
  incoming_arrows: Record<string, DiagramArrow[]>;
  outgoing_arrows: Record<string, DiagramArrow[]>;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings?: string[];
}

export interface ExecutionPlan {
  start_nodes: string[];
  has_cycles: boolean;
  cycle_nodes: string[][];
  total_nodes: number;
  total_arrows: number;
  node_types: Record<string, string>;
}

export interface ArrowValidation {
  is_valid: boolean;
  arrow: DiagramArrow;
  reason?: string;
}

export interface DependencyInfo {
  node_id: string;
  dependencies_met: boolean;
  valid_arrows: DiagramArrow[];
  missing_dependencies?: string[];
}

// Node types enum
export enum NodeType {
  START = 'startNode',
  PERSON_JOB = 'personJobNode', 
  PERSON_BATCH_JOB = 'personBatchJobNode',
  CONDITION = 'conditionNode',
  DB = 'dbNode',
  JOB = 'jobNode',
  ENDPOINT = 'endpointNode'
}