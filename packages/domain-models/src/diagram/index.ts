/**
 * Shared diagram domain models
 * These interfaces serve as the single source of truth for diagram-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import { z } from 'zod';

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
  NONE = 'none',
  ON_EVERY_TURN = 'on_every_turn',
  UPON_REQUEST = 'upon_request'
}

export enum DiagramFormat {
  NATIVE = 'native',
  LIGHT = 'light',
  READABLE = 'readable',
  NATIVE_YAML = 'native_yaml'
}

export enum DBBlockSubType {
  FIXED_PROMPT = 'fixed_prompt',
  FILE = 'file',
  CODE = 'code'
}

export enum ContentType {
  VARIABLE = 'variable',
  RAW_TEXT = 'raw_text',
  CONVERSATION_STATE = 'conversation_state'
}

export enum ContextCleaningRule {
  ON_EVERY_TURN = 'on_every_turn',
  UPON_REQUEST = 'upon_request',
  NO_FORGET = 'no_forget'
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

// Dictionary format for internal use
export interface DiagramDictFormat {
  nodes: Record<NodeID, DomainNode>;
  handles: Record<HandleID, DomainHandle>;
  arrows: Record<ArrowID, DomainArrow>;
  persons: Record<PersonID, DomainPerson>;
  apiKeys: Record<ApiKeyID, DomainApiKey>;
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
  detect_max_iterations: boolean;
  expression?: string;
  _node_indices?: string[];
}

export interface PersonJobNodeData extends BaseNodeData {
  person?: PersonID;
  firstOnlyPrompt: string;
  defaultPrompt?: string;
  maxIterations: number;
  contextCleaningRule?: string;
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
  codeType: string;
  code: string;
}

export interface UserResponseNodeData extends BaseNodeData {
  prompt: string;
  timeout: number;
}

export interface NotionNodeData extends BaseNodeData {
  operation: string;
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

// Zod schemas for validation
export const Vec2Schema = z.object({
  x: z.number(),
  y: z.number()
});

export const HandleDirectionSchema = z.nativeEnum(HandleDirection);
export const DataTypeSchema = z.nativeEnum(DataType);
export const NodeTypeSchema = z.nativeEnum(NodeType);
export const LLMServiceSchema = z.nativeEnum(LLMService);
export const ForgettingModeSchema = z.nativeEnum(ForgettingMode);

export const DomainHandleSchema = z.object({
  id: z.string(),
  nodeId: z.string(),
  label: z.string(),
  direction: HandleDirectionSchema,
  dataType: DataTypeSchema,
  position: z.string().nullable().optional()
});

export const DomainNodeSchema = z.object({
  id: z.string(),
  type: NodeTypeSchema,
  position: Vec2Schema,
  data: z.record(z.any()),
  displayName: z.string().optional()
});

export const DomainArrowSchema = z.object({
  id: z.string(),
  source: z.string(),
  target: z.string(),
  data: z.record(z.any()).nullable().optional()
});

export const DomainPersonSchema = z.object({
  id: z.string(),
  label: z.string(),
  service: LLMServiceSchema,
  model: z.string(),
  apiKeyId: z.string().nullable().optional(),
  systemPrompt: z.string().nullable().optional(),
  forgettingMode: ForgettingModeSchema,
  type: z.literal('person'),
  maskedApiKey: z.string().nullable().optional()
});

export const DomainApiKeySchema = z.object({
  id: z.string(),
  label: z.string(),
  service: LLMServiceSchema,
  key: z.string().optional(),
  maskedKey: z.string()
});

export const DiagramMetadataSchema = z.object({
  id: z.string().nullable().optional(),
  name: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  version: z.string(),
  created: z.string(),
  modified: z.string(),
  author: z.string().nullable().optional(),
  tags: z.array(z.string()).nullable().optional()
});

export const DomainDiagramSchema = z.object({
  nodes: z.array(DomainNodeSchema),
  handles: z.array(DomainHandleSchema),
  arrows: z.array(DomainArrowSchema),
  persons: z.array(DomainPersonSchema),
  apiKeys: z.array(DomainApiKeySchema),
  metadata: DiagramMetadataSchema.nullable().optional()
});

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

export function domainDiagramToDictFormat(diagram: DomainDiagram): DiagramDictFormat {
  return {
    nodes: Object.fromEntries(diagram.nodes.map(node => [node.id, node])) as Record<NodeID, DomainNode>,
    handles: Object.fromEntries(diagram.handles.map(handle => [handle.id, handle])) as Record<HandleID, DomainHandle>,
    arrows: Object.fromEntries(diagram.arrows.map(arrow => [arrow.id, arrow])) as Record<ArrowID, DomainArrow>,
    persons: Object.fromEntries(diagram.persons.map(person => [person.id, person])) as Record<PersonID, DomainPerson>,
    apiKeys: Object.fromEntries(diagram.apiKeys.map(apiKey => [apiKey.id, apiKey])) as Record<ApiKeyID, DomainApiKey>,
    metadata: diagram.metadata
  };
}

export function dictFormatToDomainDiagram(diagram: DiagramDictFormat): DomainDiagram {
  return {
    nodes: Object.values(diagram.nodes),
    handles: Object.values(diagram.handles),
    arrows: Object.values(diagram.arrows),
    persons: Object.values(diagram.persons),
    apiKeys: Object.values(diagram.apiKeys),
    metadata: diagram.metadata
  };
}

// Type guards
export function isDomainNode(obj: unknown): obj is DomainNode {
  return DomainNodeSchema.safeParse(obj).success;
}

export function isDomainDiagram(obj: unknown): obj is DomainDiagram {
  return DomainDiagramSchema.safeParse(obj).success;
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