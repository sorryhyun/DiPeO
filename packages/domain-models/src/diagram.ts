/**
 * Shared diagram domain models
 * These interfaces serve as the single source of truth for diagram-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import { LLMService, NotionOperation } from './integration.js';

// Re-export integration types for backward compatibility
export { LLMService, NotionOperation };


// Enums
export enum NodeType {
  START = 'start',
  PERSON_JOB = 'person_job',
  CONDITION = 'condition',
  JOB = 'job',
  ENDPOINT = 'endpoint',
  DB = 'db',
  USER_RESPONSE = 'user_response',
  NOTION = 'notion',
  PERSON_BATCH_JOB = 'person_batch_job'
}

export enum HandleDirection {
  INPUT = 'input',
  OUTPUT = 'output'
}

export enum DataType {
  ANY = 'any',
  STRING = 'string',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  OBJECT = 'object',
  ARRAY = 'array'
}

export enum ForgettingMode {
  NO_FORGET = 'no_forget',
  ON_EVERY_TURN = 'on_every_turn',
  UPON_REQUEST = 'upon_request'
}

export enum DiagramFormat {
  NATIVE = 'native',
  LIGHT = 'light',
  READABLE = 'readable'
}

export enum DBBlockSubType {
  FIXED_PROMPT = 'fixed_prompt',
  FILE = 'file',
  CODE = 'code',
  API_TOOL = 'api_tool'
}

export enum ContentType {
  VARIABLE = 'variable',
  RAW_TEXT = 'raw_text',
  CONVERSATION_STATE = 'conversation_state'
}

export enum SupportedLanguage {
  PYTHON = 'python',
  JAVASCRIPT = 'javascript',
  BASH = 'bash'
}

// Basic types
export interface Vec2 {
  x: number;
  y: number;
}


// Branded types for IDs
export type NodeID = string & { readonly __brand: 'NodeID' };
export type ArrowID = string & { readonly __brand: 'ArrowID' };
export type HandleID = string & { readonly __brand: 'HandleID' };
export type PersonID = string & { readonly __brand: 'PersonID' };
export type ApiKeyID = string & { readonly __brand: 'ApiKeyID' };
export type DiagramID = string & { readonly __brand: 'DiagramID' };

// Domain models
export interface DomainHandle {
  id: HandleID;
  node_id: NodeID;
  label: string;
  direction: HandleDirection;
  data_type: DataType;
  position?: string | null; // 'left' | 'right' | 'top' | 'bottom'
}

export interface DomainNode {
  id: NodeID;
  type: NodeType;
  position: Vec2;
  data: Record<string, any>;
}

export interface DomainArrow {
  id: ArrowID;
  source: HandleID; // "nodeId:handleName" format
  target: HandleID; // "nodeId:handleName" format
  content_type?: ContentType | null;
  label?: string | null;
  data?: Record<string, any> | null;
}

export interface MemoryConfig {
  forget_mode?: ForgettingMode;
  max_messages?: number;
  temperature?: number;
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
  masked_api_key?: string | null;
}

export interface DomainApiKey {
  id: ApiKeyID;
  label: string;
  service: LLMService;
  key?: string; // Excluded from serialization by default
  masked_key: string;
}

export interface DiagramMetadata {
  id?: DiagramID | null;
  name?: string | null;
  description?: string | null;
  version: string;
  created: string; // ISO datetime string
  modified: string; // ISO datetime string
  author?: string | null;
  tags?: string[] | null;
}

// Main diagram type used in GraphQL API (array format)
export interface DomainDiagram {
  nodes: DomainNode[];
  handles: DomainHandle[];
  arrows: DomainArrow[];
  persons: DomainPerson[];
  metadata?: DiagramMetadata | null;
}


// Node data schemas - can be extended per node type
export interface BaseNodeData {
  label: string;
  flipped?: boolean;
  [key: string]: unknown;
}

export interface StartNodeData extends BaseNodeData {
  custom_data: Record<string, string | number | boolean>;
  output_data_structure: Record<string, string>;
}

export interface ConditionNodeData extends BaseNodeData {
  condition_type: string;
  expression?: string;
  node_indices?: string[];
}

export interface PersonJobNodeData extends BaseNodeData {
  person?: PersonID;
  first_only_prompt: string;
  default_prompt?: string;
  max_iteration: number;
  memory_config?: MemoryConfig | null;
}

export interface EndpointNodeData extends BaseNodeData {
  save_to_file: boolean;
  file_name?: string;
}

export interface DBNodeData extends BaseNodeData {
  file?: string;
  collection?: string;
  sub_type: DBBlockSubType;
  operation: string;
  query?: string;
  data?: Record<string, any>;
}

export interface JobNodeData extends BaseNodeData {
  code_type: SupportedLanguage;
  code: string;
}

export interface UserResponseNodeData extends BaseNodeData {
  prompt: string;
  timeout: number;
}

export interface NotionNodeData extends BaseNodeData {
  operation: NotionOperation;
  page_id?: string;
  database_id?: string;
}

export type PersonBatchJobNodeData = PersonJobNodeData;


