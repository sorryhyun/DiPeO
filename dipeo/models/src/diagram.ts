/**
 * Shared diagram domain models
 * These interfaces serve as the single source of truth for diagram-related types
 * Used by both frontend (TypeScript) and backend (Python via code generation)
 */

import { LLMService, APIServiceType, NotionOperation, ToolConfig } from './integration.js';

// Re-export integration types for backward compatibility
export { LLMService, APIServiceType, NotionOperation };
export type { ToolConfig };


// Enums
export enum NodeType {
  START = 'start',
  PERSON_JOB = 'person_job',
  CONDITION = 'condition',
  JOB = 'job',  // Deprecated: use CODE_JOB or API_JOB instead
  CODE_JOB = 'code_job',
  API_JOB = 'api_job',
  ENDPOINT = 'endpoint',
  DB = 'db',
  USER_RESPONSE = 'user_response',
  NOTION = 'notion',
  PERSON_BATCH_JOB = 'person_batch_job',
  HOOK = 'hook',
  TEMPLATE_JOB = 'template_job',
  JSON_SCHEMA_VALIDATOR = 'json_schema_validator'
}

export enum HandleDirection {
  INPUT = 'input',
  OUTPUT = 'output'
}

export enum HandleLabel {
  DEFAULT = 'default',
  FIRST = 'first',
  CONDITION_TRUE = 'condtrue',
  CONDITION_FALSE = 'condfalse',
  SUCCESS = 'success',
  ERROR = 'error'
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

export enum MemoryView {
  ALL_INVOLVED = 'all_involved',  // Messages where person is sender or recipient
  SENT_BY_ME = 'sent_by_me',      // Messages I sent
  SENT_TO_ME = 'sent_to_me',      // Messages sent to me
  SYSTEM_AND_ME = 'system_and_me', // System messages and my interactions
  CONVERSATION_PAIRS = 'conversation_pairs', // Request/response pairs
  ALL_MESSAGES = 'all_messages',  // All messages in conversation (for judges/observers)
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
  RAW_TEXT = 'raw_text',
  CONVERSATION_STATE = 'conversation_state',
  OBJECT = 'object'
}

export enum SupportedLanguage {
  PYTHON = 'python',
  TYPESCRIPT = 'typescript',
  BASH = 'bash',
  SHELL = 'shell'
}

export enum HttpMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  DELETE = 'DELETE',
  PATCH = 'PATCH'
}

export enum HookType {
  SHELL = 'shell',
  WEBHOOK = 'webhook',
  PYTHON = 'python',
  FILE = 'file'
}

export enum HookTriggerMode {
  MANUAL = 'manual',
  HOOK = 'hook'
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
  label: HandleLabel;
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
  source: HandleID; // "nodeId_handleName_direction" format
  target: HandleID; // "nodeId_handleName_direction" format
  content_type?: ContentType | null;
  label?: string | null;
  data?: Record<string, any> | null;
}

export interface MemoryConfig {
  forget_mode?: ForgettingMode;
  max_messages?: number;
  temperature?: number;
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
  key?: string; // Excluded from serialization by default
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
  trigger_mode?: HookTriggerMode;
  hook_event?: string;  // Event name to listen for when trigger_mode is 'hook'
  hook_filters?: Record<string, any>;  // Filters to match specific events
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
  memory_config?: MemoryConfig | null;  // Deprecated - use memory_settings
  memory_settings?: MemorySettings | null;  // New unified memory configuration
  tools?: ToolConfig[] | null;
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

export interface CodeJobNodeData extends BaseNodeData {
  language: SupportedLanguage;
  filePath: string;
  functionName?: string;  // Function to call (default: 'main' for Python)
  timeout?: number;  // in seconds
}

export interface ApiJobNodeData extends BaseNodeData {
  url: string;
  method: HttpMethod;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  body?: any;
  timeout?: number;  // in seconds
  auth_type?: 'none' | 'bearer' | 'basic' | 'api_key';
  auth_config?: Record<string, string>;
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

export interface HookNodeData extends BaseNodeData {
  hook_type: HookType;
  config: {
    // For shell hooks
    command?: string;
    args?: string[];
    env?: Record<string, string>;
    cwd?: string;
    
    // For webhook hooks
    url?: string;
    method?: HttpMethod;
    headers?: Record<string, string>;
    
    // For Python hooks
    script?: string;
    function_name?: string;
    
    // For file hooks  
    file_path?: string;
    format?: 'json' | 'yaml' | 'text';
  };
  timeout?: number;  // in seconds
  retry_count?: number;
  retry_delay?: number;  // in seconds
}


export interface TemplateJobNodeData extends BaseNodeData {
  template_path?: string;  // Path to template file
  template_content?: string;  // Inline template content
  output_path?: string;  // Where to write the rendered output
  variables?: Record<string, any>;  // Variables to pass to the template
  engine?: 'internal' | 'jinja2' | 'handlebars';  // Template engine (default: internal)
}

export interface ShellJobNodeData extends BaseNodeData {
  command: string;  // Shell command to execute
  args?: string[];  // Command arguments
  cwd?: string;  // Working directory
  env?: Record<string, string>;  // Environment variables
  timeout?: number;  // Execution timeout in seconds
  capture_output?: boolean;  // Whether to capture stdout/stderr
  shell?: boolean;  // Whether to run through shell
}

export interface JsonSchemaValidatorNodeData extends BaseNodeData {
  schema_path?: string;  // Path to JSON schema file
  schema?: Record<string, any>;  // Inline schema definition
  data_path?: string;  // Path to data file to validate
  strict_mode?: boolean;  // Whether to use strict validation
  error_on_extra?: boolean;  // Error on extra properties
}

