/**
 * Shared diagram domain models
 * These interfaces serve as the single source of truth for diagram-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */


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

export enum LLMService {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
  GROK = 'grok',
  BEDROCK = 'bedrock',
  VERTEX = 'vertex',
  DEEPSEEK = 'deepseek'
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

export enum NotionOperation {
  CREATE_PAGE = 'create_page',
  UPDATE_PAGE = 'update_page',
  READ_PAGE = 'read_page',
  DELETE_PAGE = 'delete_page',
  CREATE_DATABASE = 'create_database',
  QUERY_DATABASE = 'query_database',
  UPDATE_DATABASE = 'update_database'
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
  nodeId: NodeID;
  label: string;
  direction: HandleDirection;
  dataType: DataType;
  position?: string | null; // 'left' | 'right' | 'top' | 'bottom'
}

export interface DomainNode {
  id: NodeID;
  type: NodeType;
  position: Vec2;
  data: Record<string, any>;
  displayName?: string;
}

export interface DomainArrow {
  id: ArrowID;
  source: HandleID; // "nodeId:handleName" format
  target: HandleID; // "nodeId:handleName" format
  data?: Record<string, any> | null;
}

export interface DomainPerson {
  id: PersonID;
  label: string;
  service: LLMService;
  model: string;
  apiKeyId?: ApiKeyID | null;
  systemPrompt?: string | null;
  forgettingMode: ForgettingMode;
  type: 'person';
  maskedApiKey?: string | null;
}

export interface DomainApiKey {
  id: ApiKeyID;
  label: string;
  service: LLMService;
  key?: string; // Excluded from serialization by default
  maskedKey: string;
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
  apiKeys: DomainApiKey[];
  metadata?: DiagramMetadata | null;
}


// Node data schemas - can be extended per node type
export interface BaseNodeData {
  label: string;
  flipped?: boolean;
  [key: string]: unknown;
}

export interface StartNodeData extends BaseNodeData {
  customData: Record<string, string | number | boolean>;
  outputDataStructure: Record<string, string>;
}

export interface ConditionNodeData extends BaseNodeData {
  conditionType: string;
  expression?: string;
  node_indices?: string[];
}

export interface PersonJobNodeData extends BaseNodeData {
  person?: PersonID;
  firstOnlyPrompt: string;
  defaultPrompt?: string;
  maxIteration: number;
  forgettingMode?: string;
}

export interface EndpointNodeData extends BaseNodeData {
  saveToFile: boolean;
  fileName?: string;
}

export interface DBNodeData extends BaseNodeData {
  file?: string;
  collection?: string;
  subType: DBBlockSubType;
  operation: string;
  query?: string;
  data?: Record<string, any>;
}

export interface JobNodeData extends BaseNodeData {
  codeType: SupportedLanguage;
  code: string;
}

export interface UserResponseNodeData extends BaseNodeData {
  prompt: string;
  timeout: number;
}

export interface NotionNodeData extends BaseNodeData {
  operation: NotionOperation;
  pageId?: string;
  databaseId?: string;
}

export type PersonBatchJobNodeData = PersonJobNodeData;

// Node data mapping
export type NodeDataMap = {
  [NodeType.START]: StartNodeData;
  [NodeType.CONDITION]: ConditionNodeData;
  [NodeType.PERSON_JOB]: PersonJobNodeData;
  [NodeType.ENDPOINT]: EndpointNodeData;
  [NodeType.DB]: DBNodeData;
  [NodeType.JOB]: JobNodeData;
  [NodeType.USER_RESPONSE]: UserResponseNodeData;
  [NodeType.NOTION]: NotionNodeData;
  [NodeType.PERSON_BATCH_JOB]: PersonBatchJobNodeData;
};


// Utility functions
export function createEmptyDiagram(): DomainDiagram {
  return {
    nodes: [],
    handles: [],
    arrows: [],
    persons: [],
    apiKeys: [],
    metadata: {
      version: '2.0.0',
      created: new Date().toISOString(),
      modified: new Date().toISOString()
    }
  };
}


// Type guards
export function isDomainNode(obj: unknown): obj is DomainNode {
  // Simple type guard without Zod
  if (!obj || typeof obj !== 'object') return false;
  const node = obj as any;
  return (
    typeof node.id === 'string' &&
    typeof node.type === 'string' &&
    node.position &&
    typeof node.position.x === 'number' &&
    typeof node.position.y === 'number' &&
    node.data &&
    typeof node.data === 'object'
  );
}

// Handle utilities
export function parseHandleId(handleId: HandleID): { nodeId: NodeID; handleName: string } {
  const [nodeId, ...handleNameParts] = handleId.split(':');
  return {
    nodeId: nodeId as NodeID,
    handleName: handleNameParts.join(':')
  };
}

export function createHandleId(nodeId: NodeID, handleName: string): HandleID {
  return `${nodeId}:${handleName}` as HandleID;
}

export function areHandlesCompatible(source: DomainHandle, target: DomainHandle): boolean {
  // Basic compatibility: output can connect to input
  if (source.direction !== HandleDirection.OUTPUT || target.direction !== HandleDirection.INPUT) {
    return false;
  }
  
  // Type compatibility
  if (source.dataType === DataType.ANY || target.dataType === DataType.ANY) {
    return true;
  }
  
  return source.dataType === target.dataType;
}