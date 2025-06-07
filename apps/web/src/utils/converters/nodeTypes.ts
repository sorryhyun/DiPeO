import { NodeType } from '@/types';

// Base node properties shared by all nodes
interface BaseNodeData {
  id: string;
  label: string;
  type: NodeType;
}

// Discriminated union for node-specific data
export interface StartNodeData extends BaseNodeData {
  type: 'start';
}

export interface PersonJobNodeData extends BaseNodeData {
  type: 'person_job';
  personId?: string;
  defaultPrompt: string;
  firstOnlyPrompt: string;
  contextCleaningRule: 'no_forget' | 'on_every_turn' | 'upon_request';
  maxIterations?: number;
  mode: 'sync' | 'async';
  detectedVariables: string[];
}

export interface ConditionNodeData extends BaseNodeData {
  type: 'condition';
  conditionType: 'expression' | 'detect_max_iterations';
  expression: string;
  maxIterations?: number;
}

export interface DbNodeData extends BaseNodeData {
  type: 'db';
  subType: 'file' | 'fixed_prompt' | 'database';
  sourceDetails: string;
}

export interface JobNodeData extends BaseNodeData {
  type: 'job';
  subType: 'code' | 'script';
  sourceDetails: string;
}

export interface EndpointNodeData extends BaseNodeData {
  type: 'endpoint';
  saveToFile: boolean;
  filePath: string;
  fileFormat: 'text' | 'json' | 'yaml';
}

export interface NotionNodeData extends BaseNodeData {
  type: 'notion';
  subType: 'read' | 'write';
  pageId: string;
  properties: Record<string, any>;
}

export interface PersonBatchJobNodeData extends BaseNodeData {
  type: 'person_batch_job';
  personId?: string;
  defaultPrompt: string;
  firstOnlyPrompt: string;
  contextCleaningRule: 'no_forget' | 'on_every_turn' | 'upon_request';
  mode: 'sync' | 'async';
  detectedVariables: string[];
}

export interface UserResponseNodeData extends BaseNodeData {
  type: 'user_response';
  promptMessage: string;
  timeoutSeconds: number;
}

// Union type for all node data types
export type DiagramNodeData = 
  | StartNodeData
  | PersonJobNodeData
  | ConditionNodeData
  | DbNodeData
  | JobNodeData
  | EndpointNodeData
  | NotionNodeData
  | PersonBatchJobNodeData
  | UserResponseNodeData;

// Type-safe node with generics
export interface TypedNode<T extends DiagramNodeData = DiagramNodeData> {
  id: string;
  type: T['type'];
  position: { x: number; y: number };
  data: T;
}

// Helper type to get node data by type
export type NodeDataByType<T extends NodeType> = Extract<DiagramNodeData, { type: T }>;

// Helper function to assert node type
export function isNodeType<T extends NodeType>(
  node: TypedNode,
  type: T
): node is TypedNode<NodeDataByType<T>> {
  return node.type === type;
}

// Constants for node type names
export const NODE_TYPE_NAMES = {
  start: 'start',
  person_job: 'person_job',
  condition: 'condition',
  db: 'db',
  job: 'job',
  endpoint: 'endpoint',
  notion: 'notion',
  person_batch_job: 'person_batch_job',
  user_response: 'user_response'
} as const;

// Type for node type names
export type NodeTypeName = typeof NODE_TYPE_NAMES[keyof typeof NODE_TYPE_NAMES];