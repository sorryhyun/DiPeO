// Node-related types
import { Node as ReactFlowNode } from '@xyflow/react';
import { ApiKey } from './api';

export type NodeType = 
  | 'start'
  | 'person_job'
  | 'person_batch_job' 
  | 'condition'
  | 'db'
  | 'job'
  | 'endpoint';

export interface Position {
  x: number;
  y: number;
}

// Base for all canvas blocks (nodes) with discriminating `type`
export interface BaseBlockData {
  id: string;
  type: NodeType;
  label: string;
  flipped?: boolean;
  [key: string]: unknown; // For React Flow compatibility
}

export interface StartBlockData extends BaseBlockData {
  type: 'start';
  description?: string;
}

export interface PersonJobBlockData extends BaseBlockData {
  type: 'person_job';
  personId?: string;
  llmApi?: ApiKey['service'];
  apiKeyId?: ApiKey['id'];
  modelName?: string;
  defaultPrompt?: string;
  firstOnlyPrompt?: string;
  detectedVariables?: string[];
  contextCleaningRule?: 'uponRequest' | 'noForget' | 'onEveryTurn';
  contextCleaningTurns?: number;
  iterationCount?: number;
}

export interface PersonBatchJobBlockData extends BaseBlockData {
  type: 'person_batch_job';
  personId?: string;
  llmApi?: ApiKey['service'];
  apiKeyId?: ApiKey['id'];
  modelName?: string;
  batchPrompt?: string;
  batchSize?: number;
  parallelProcessing?: boolean;
  aggregationMethod?: 'concatenate' | 'summarize' | 'custom';
  customAggregationPrompt?: string;
  detectedVariables?: string[];
  iterationCount?: number;
}

export type JobBlockSubType = 'api_tool' | 'diagram_link' | 'code';
export interface JobBlockData extends BaseBlockData {
  type: 'job';
  subType: JobBlockSubType;
  sourceDetails: string;
  iterationCount?: number;
  firstOnlyPrompt?: string;
  description?: string;
}

export type DBBlockSubType = 'fixed_prompt' | 'file';
export interface DBBlockData extends BaseBlockData {
  type: 'db';
  subType: DBBlockSubType;
  sourceDetails: string;
  description?: string;
}

export type ConditionType = 'expression' | 'max_iterations';
export interface ConditionBlockData extends BaseBlockData {
  type: 'condition';
  conditionType: ConditionType;
  expression?: string;
  maxIterations?: number;
}

export interface EndpointBlockData extends BaseBlockData {
  type: 'endpoint';
  description?: string;
  // Optional file save properties
  saveToFile?: boolean;
  filePath?: string;
  fileFormat?: 'json' | 'text' | 'csv';
}

// Union type for all block data types  
export type DiagramNodeData = StartBlockData | PersonJobBlockData | PersonBatchJobBlockData | JobBlockData | DBBlockData | ConditionBlockData | EndpointBlockData;

// Unified Node interface combining execution.ts and domain.ts patterns
export interface NodeData {
  id: string;
  type: NodeType;
  label: string;
  // Additional properties handled by specific node data types
}

export interface Node {
  id: string;
  type: NodeType;
  position: Position;
  data: NodeData;
}

// Type for diagram nodes with React Flow compatibility
export type DiagramNode = ReactFlowNode<DiagramNodeData & Record<string, unknown>>;