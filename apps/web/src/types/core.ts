/**
 * Core types for DiPeO
 * Single source of truth for all fundamental types
 */

import type { NodeKind } from './primitives/enums';
import type { Vec2 } from './primitives/basic';
import type { NodeID, ArrowID, PersonID, HandleID } from './branded';

// Re-export node data types for convenience
export type { 
  StartNodeData,
  ConditionNodeData,
  PersonJobNodeData,
  EndpointNodeData,
  DBNodeData,
  JobNodeData,
  UserResponseNodeData,
  NotionNodeData,
  PersonBatchJobNodeData
} from './domain/node';

/**
 * Core node data union type
 * Maps node types to their specific data structures
 */
export type NodeData = {
  start: import('./domain/node').StartNodeData;
  condition: import('./domain/node').ConditionNodeData;
  person_job: import('./domain/node').PersonJobNodeData;
  endpoint: import('./domain/node').EndpointNodeData;
  db: import('./domain/node').DBNodeData;
  job: import('./domain/node').JobNodeData;
  user_response: import('./domain/node').UserResponseNodeData;
  notion: import('./domain/node').NotionNodeData;
  person_batch_job: import('./domain/node').PersonBatchJobNodeData;
};

/**
 * Core domain node interface
 * This is the fundamental node structure used throughout the application
 */
export interface DomainNode<T extends NodeKind = NodeKind> {
  id: NodeID;
  type: T;
  position: Vec2;
  data: T extends keyof NodeData ? NodeData[T] : Record<string, unknown>;
}

/**
 * Node execution state
 * Tracks runtime state during diagram execution
 */
export interface NodeExecutionState {
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'paused';
  error?: string;
  timestamp: number;
  skipReason?: string;
  tokenCount?: number;
  progress?: string;
}

/**
 * Arrow (edge/connection) interface
 */
export interface DomainArrow {
  id: ArrowID;
  source: string; // Format: "nodeId:handleName"
  target: string; // Format: "nodeId:handleName"
  data?: Record<string, unknown>;
}

/**
 * Handle interface for node connections
 * Re-export from domain for consistency
 */
export type { DomainHandle } from './domain/handle';

/**
 * Person (LLM instance) interface
 */
export interface DomainPerson {
  id: PersonID;
  label: string;
  service: string;
  model: string;
  maxTokens?: number;
  temperature?: number;
  forgettingMode: 'no_forget' | 'adaptive' | 'aggressive';
  systemPrompt?: string;
}

/**
 * Diagram structure
 * Complete representation of a DiPeO diagram
 */
export interface DomainDiagram {
  nodes: Record<NodeID, DomainNode>;
  arrows: Record<ArrowID, DomainArrow>;
  persons: Record<PersonID, DomainPerson>;
  handles: Record<NodeID, DomainHandle[]>;
  metadata?: {
    name?: string;
    description?: string;
    version?: string;
    created?: string;
    modified?: string;
  };
}

/**
 * Type guard functions
 */
export const isDomainNode = (obj: unknown): obj is DomainNode => {
  return typeof obj === 'object' && 
    obj !== null && 
    'id' in obj && 
    'type' in obj && 
    'position' in obj && 
    'data' in obj;
};

export const isDomainArrow = (obj: unknown): obj is DomainArrow => {
  return typeof obj === 'object' && 
    obj !== null && 
    'id' in obj && 
    'source' in obj && 
    'target' in obj;
};

export const isDomainPerson = (obj: unknown): obj is DomainPerson => {
  return typeof obj === 'object' && 
    obj !== null && 
    'id' in obj && 
    'label' in obj && 
    'service' in obj && 
    'model' in obj;
};

/**
 * Utility types for working with nodes
 */
export type NodeOfType<T extends NodeKind> = DomainNode<T>;
export type NodeDataOfType<T extends NodeKind> = T extends keyof NodeData ? NodeData[T] : never;
export type AnyDomainNode = DomainNode<NodeKind>;