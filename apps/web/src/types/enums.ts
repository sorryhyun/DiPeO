// Centralized enum definitions for the type system

// Node types - matches the system's node kinds
export enum NodeType {
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

// Data types for handle connections
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

// Arrow types for ReactFlow
export enum ArrowType {
  Default = 'default',
  Straight = 'straight',
  Step = 'step',
  SmoothStep = 'smoothstep',
  Bezier = 'bezier'
}

// Handle positions
export enum HandlePosition {
  Top = 'top',
  Right = 'right',
  Bottom = 'bottom',
  Left = 'left'
}

// Execution states for nodes
export enum NodeExecutionState {
  Idle = 'idle',
  Running = 'running',
  Success = 'success',
  Error = 'error',
  Paused = 'paused',
  Skipped = 'skipped'
}

// Connection validation modes
export enum ConnectionMode {
  Strict = 'strict',
  Loose = 'loose',
  Any = 'any'
}