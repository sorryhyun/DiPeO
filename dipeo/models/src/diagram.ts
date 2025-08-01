/**
 * Shared diagram domain models
 * These interfaces serve as the single source of truth for diagram-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import { LLMService, APIServiceType, NotionOperation, ToolConfig } from './integration.js';
import { 
  NodeType, HandleDirection, HandleLabel, DataType, MemoryView, 
  ContentType
} from './enums.js';

export { LLMService, APIServiceType, NotionOperation };
export type { ToolConfig };
export * from './node-data';
export * from './enums.js';
export interface Vec2 {
  x: number;
  y: number;
}


export type NodeID = string & { readonly __brand: 'NodeID' };
export type ArrowID = string & { readonly __brand: 'ArrowID' };
export type HandleID = string & { readonly __brand: 'HandleID' };
export type PersonID = string & { readonly __brand: 'PersonID' };
export type ApiKeyID = string & { readonly __brand: 'ApiKeyID' };
export type DiagramID = string & { readonly __brand: 'DiagramID' };

export interface DomainHandle {
  id: HandleID;
  node_id: NodeID;
  label: HandleLabel;
  direction: HandleDirection;
  data_type: DataType;
  position?: string | null;
}

export interface DomainNode {
  id: NodeID;
  type: NodeType;
  position: Vec2;
  data: Record<string, any>;
}

export interface DomainArrow {
  id: ArrowID;
  source: HandleID;
  target: HandleID;
  content_type?: ContentType | null;
  label?: string | null;
  data?: Record<string, any> | null;
}

export interface MemorySettings {
  view: MemoryView;
  max_messages?: number | null;
  preserve_system?: boolean;
}

export interface PersonLLMConfig {
  service: LLMService;
  model: string;
  api_key_id: ApiKeyID;
  system_prompt?: string | null;
}

export interface DomainPerson {
  id: PersonID;
  label: string;
  llm_config: PersonLLMConfig;
  type: 'person';
}

export interface DomainApiKey {
  id: ApiKeyID;
  label: string;
  service: APIServiceType;
  key?: string;
}

export interface DiagramMetadata {
  id?: DiagramID | null;
  name?: string | null;
  description?: string | null;
  version: string;
  created: string;
  modified: string;
  author?: string | null;
  tags?: string[] | null;
  format?: string | null;
}

export interface DomainDiagram {
  nodes: DomainNode[];
  handles: DomainHandle[];
  arrows: DomainArrow[];
  persons: DomainPerson[];
  metadata?: DiagramMetadata | null;
}


export interface BaseNodeData {
  label: string;
  flipped?: boolean;
  [key: string]: unknown;
}


