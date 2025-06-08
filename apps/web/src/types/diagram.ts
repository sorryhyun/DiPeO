// types/diagram.ts - Diagram domain types

import type { ID, Vec2, Dict } from './primitives';

export const NodeKinds = [
  'start', 'job', 'person_job', 'condition', 'endpoint', 'db', 'notion',
  'person_batch_job', 'user_response',
] as const;
export type NodeKind = typeof NodeKinds[number];


// Handle definition for node connection points
export interface Handle {
  id: ID;  // Globally unique, e.g., "node1:output"
  nodeId: ID;  // Reference to parent node
  kind: 'source' | 'target';  // More semantic than 'type'
  name: string;  // Handle name for identification
  position?: 'top' | 'right' | 'bottom' | 'left';
  dataType?: string;  // For type-checking connections
  label?: string;
  style?: Record<string, any>;
}

// Note: This extends ReactFlow's Node type structure for compatibility
export interface Node<D = Dict, K extends NodeKind = NodeKind> {
  id: ID;
  type: K;  // ReactFlow requires 'type' property
  position: Vec2;  // ReactFlow requires 'position' property
  data: D & { 
    type: K;
  };
  handles: Handle[];  // Explicitly defined handles (required, not optional)
}


/** Lightweight edge between handles */
export interface Arrow {
  id: ID;
  source: ID;  // Handle ID (not node ID)
  target: ID;  // Handle ID (not node ID)
  data?: ArrowData;  // ReactFlow pattern - data goes here
}

export interface ArrowData {
  label?: string;
  condition?: string;
  variable?: string;
  controlPointOffsetX?: number;
  controlPointOffsetY?: number;
  loopRadius?: number;
  branch?: string;
  contentType?: string;
}

export interface ApiKey {
  id: ID;
  service: string;
  key: string;
  name?: string;
}

export interface Diagram {
  id: string;
  name: string;
  description?: string;
  nodes: Node[];
  arrows: Arrow[];
  persons: Person[];
  apiKeys: ApiKey[];
  metadata?: Dict;
}

/* Person / Memory */
export interface Person {
  id: ID;
  label: string;
  apiKeyId?: string;
  modelName?: string;
  systemPrompt?: string;
  memory?: ConversationMessage[];
  options?: Record<string, any>;
  avatarUrl?: string;
}

export interface ConversationMessage {
  id?: ID;
  role: 'user' | 'assistant' | 'system';
  personId: ID;
  content: string;
  timestamp?: string;
  tokenCount?: number;
  nodeLabel?: string;
}

export interface Page<T = unknown> {
  items: T[];
  total: number;
  hasMore: boolean;
}

export interface PersonMemoryState {
  messages: ConversationMessage[];
  totalMessages: number;
  visibleMessages: number;
  forgottenMessages: number;
  hasMore: boolean;
  visible: number;
  forgotten: number;
}

export interface DiagramData {
  nodes: any[];
  arrows: any[];
  persons: any[];
  apiKeys: any[];
  metadata?: Record<string, any>;
}

// Handle ID utilities
export type HandleID = `${string}:${string}`;  // Format: "nodeId:handleName"

// Type for ReactFlow edge conversion
export interface ReactFlowEdge {
  id: string;
  source: string;  // Node ID
  target: string;  // Node ID
  sourceHandle?: string;  // Handle name
  targetHandle?: string;  // Handle name
  data?: ArrowData;
}