import {NodeID, PersonID} from '../branded';
import { Vec2, NodeKind, ConditionType, PersonForgettingStrategy, JobLanguage, DBOperation, DBSubType, NotionOperation, ProcessType } from '../primitives';

export interface DomainNode {
  id: NodeID;
  type: NodeKind;
  position: Vec2;
  data: Record<string, unknown>;
}

export interface TypedDomainNode<T extends NodeKind, D extends Record<string, unknown> = NodeData>
  extends DomainNode {
  type: T;
  data: D;
}

export interface StartNodeData {
  label: string;
  customData: { [key: string]: string | number | boolean };
  outputDataStructure: { [key: string]: string };
  flipped?: boolean;
  [key: string]: unknown; // Allow additional properties
}

export type StartNode = TypedDomainNode<NodeKind, StartNodeData> & { type: 'start' };

export interface ConditionNodeData {
  label: string;
  conditionType: ConditionType;
  detect_max_iterations: boolean;
  expression?: string;
  _node_indices?: string[];
  flipped?: boolean;
  [key: string]: unknown; // Allow additional properties
}

export type ConditionNode = TypedDomainNode<NodeKind, ConditionNodeData> & { type: 'condition' };

export interface PersonJobNodeData {
  label: string;
  person?: PersonID;
  firstOnlyPrompt: string;
  defaultPrompt?: string;
  maxIterations: number;
  contextCleaningRule?: PersonForgettingStrategy;
  flipped?: boolean;
  [key: string]: unknown; // Allow additional properties
}

export type PersonJobNode = TypedDomainNode<NodeKind, PersonJobNodeData> & { type: 'person_job' };

export interface EndpointNodeData {
  label: string;
  saveToFile: boolean;
  fileName?: string;
  flipped?: boolean;
  [key: string]: unknown; // Allow additional properties
}

export type EndpointNode = TypedDomainNode<NodeKind, EndpointNodeData> & { type: 'endpoint' };

export interface DBNodeData {
  label: string;
  file?: string;
  collection?: string;
  subType: DBSubType;
  operation: DBOperation;
  query?: string;
  data?: { [key: string]: any };
  flipped?: boolean;
  [key: string]: unknown; // Allow additional properties
}

export type DBNode = TypedDomainNode<NodeKind, DBNodeData> & { type: 'db' };

export interface JobNodeData {
  label: string;
  codeType: JobLanguage;
  code: string;
  flipped?: boolean;
  [key: string]: unknown; // Allow additional properties
}

export type JobNode = TypedDomainNode<NodeKind, JobNodeData> & { type: 'job' };

export interface UserResponseNodeData {
  label: string;
  prompt: string;
  timeout: number;
  flipped?: boolean;
  [key: string]: unknown; // Allow additional properties
}

export type UserResponseNode = TypedDomainNode<NodeKind, UserResponseNodeData> & { type: 'user_response' };

export interface NotionNodeData {
  label: string;
  operation: NotionOperation | 'create' | 'update';
  pageId?: string;
  databaseId?: string;
  title?: string;
  content?: string;
  flipped?: boolean;
  [key: string]: unknown; // Allow additional properties
}

export type NotionNode = TypedDomainNode<NodeKind, NotionNodeData> & { type: 'notion' };

export interface PersonBatchJobNodeData {
  label: string;
  person?: PersonID;
  process_type: ProcessType;
  basePrompt: string;
  outputStructure: { [key: string]: string };
  contextCleaningRule?: PersonForgettingStrategy;
  parallelism: number;
  flipped?: boolean;
  [key: string]: unknown; // Allow additional properties
}

export type PersonBatchJobNode = TypedDomainNode<NodeKind, PersonBatchJobNodeData> & { type: 'person_batch_job' };

export type NodeData = 
  | StartNodeData
  | ConditionNodeData
  | PersonJobNodeData
  | EndpointNodeData
  | DBNodeData
  | JobNodeData
  | UserResponseNodeData
  | NotionNodeData
  | PersonBatchJobNodeData;

export type DiagramNode = 
  | StartNode
  | ConditionNode
  | PersonJobNode
  | EndpointNode
  | DBNode
  | JobNode
  | UserResponseNode
  | NotionNode
  | PersonBatchJobNode;

export function isDomainNode(obj: unknown): obj is DomainNode {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'id' in obj &&
    'type' in obj &&
    'position' in obj &&
    'data' in obj
  );
}

export function isNodeOfKind<T extends NodeKind>(
  node: DomainNode,
  type: T
): node is Extract<DiagramNode, { type: T }> {
  return node.type === type;
}