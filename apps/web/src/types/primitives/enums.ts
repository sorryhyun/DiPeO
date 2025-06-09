/**
 * Centralized enum definitions for the type system
 */

export enum NodeKind {
  Start = 'start',
  Condition = 'condition',
  PersonJob = 'person_job',
  Endpoint = 'endpoint',
  DB = 'db',
  Job = 'job',
  UserResponse = 'user_response',
  Notion = 'notion',
  PersonBatchJob = 'person_batch_job'
}

export enum DataType {
  Any = 'any',
  String = 'string',
  Number = 'number',
  Boolean = 'boolean',
  Array = 'array',
  Object = 'object',
  Text = 'text',
  Integer = 'integer',
  Float = 'float',
  JSON = 'json'
}

export enum ArrowKind {
  Default = 'default',
  Straight = 'straight',
  Step = 'step',
  SmoothStep = 'smoothstep',
  Bezier = 'bezier'
}

export enum HandlePosition {
  Top = 'top',
  Right = 'right',
  Bottom = 'bottom',
  Left = 'left'
}

export enum NodeExecutionState {
  Pending = 'pending',
  Running = 'running',
  Completed = 'completed',
  Failed = 'failed',
  Skipped = 'skipped',
  Paused = 'paused'
}

export enum ConnectionMode {
  Strict = 'strict',
  Loose = 'loose'
}

export enum PersonForgettingStrategy {
  NoForget = 'no_forget',
  OnEveryTurn = 'on_every_turn',
  UponRequest = 'upon_request'
}

export enum PersonService {
  OpenAI = 'openai',
  Claude = 'claude',
  Gemini = 'gemini',
  Grok = 'grok',
  Custom = 'custom'
}

export enum JobLanguage {
  Python = 'python',
  JavaScript = 'javascript',
  Bash = 'bash'
}

export enum DBOperation {
  Save = 'save',
  Load = 'load',
  Delete = 'delete',
  Update = 'update',
  Query = 'query'
}

export enum NotionOperation {
  Read = 'read',
  Write = 'write'
}