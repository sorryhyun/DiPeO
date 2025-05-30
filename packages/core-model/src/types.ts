// --- File: packages/core-model/src/types.ts ---
// (Expanded and corrected)
import {Node, Edge, OnEdgesChange, EdgeChange, Connection,
  applyEdgeChanges as applyEdgeChangesRF,
  addEdge as addEdgeRF
} from '@xyflow/react';


export interface ApiKey {
  id: string;
  name: string;
  service: 'claude' | 'chatgpt' | 'grok' | 'gemini' | 'custom';
  // Key itself should NOT be stored in frontend state directly if possible,
  // rather managed by a secure backend or encrypted in browser storage.
  keyReference?: string;
}

export type ArrowKind = 'normal' | 'fixed';
export type BlockType = 'start' | 'person_job' | 'db' | 'job' | 'condition' | 'endpoint' ; // db_target is deprecated

// Base for all canvas blocks (nodes) with discriminating `type`
export interface BaseBlockData {
  // Satisfy Record<string, unknown> for React Flow
  [key: string]: unknown;

  id: string;
  type: BlockType;
  label: string;
  flipped?: boolean;
}

export interface StartBlockData extends BaseBlockData {
  type: 'start';
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
  mode?: 'sync' | 'batch';
  contextCleaningRule?: 'upon_request' | 'no_forget' | 'on_every_turn';
  contextCleaningTurns?: number;
  iterationCount?: number;
}

export type JobBlockSubType = 'api_tool' | 'diagram_link' | 'code';
export interface JobBlockData extends BaseBlockData {
  type: 'job';
  subType: JobBlockSubType;
  sourceDetails: string;
}

export type DBBlockSubType = 'fixed_prompt' | 'file';


export interface DBBlockData extends BaseBlockData {
  type: 'db';
  subType: DBBlockSubType;
  sourceDetails: string;
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
  // Optional file save properties
  saveToFile?: boolean;
  filePath?: string;
  fileFormat?: 'json' | 'text' | 'csv';
}

// Person definitions live outside the canvas; used to configure LLM settings
export interface PersonDefinition {
  id: string;
  label: string;
  service?: ApiKey['service'];
  apiKeyId?: ApiKey['id'];
  modelName?: string;
  systemPrompt?: string;
}

export interface ArrowData {
  [key: string]: unknown;
  id: string;
  sourceBlockId: string;
  targetBlockId: string;
  sourceHandleId?: string;
  targetHandleId?: string;
  label?: string;
  contentType?: 'raw_text' | 'variable_in_object' | 'conversation_state';
  arrowKind?: ArrowKind;
  variableName?: string;
  objectKeyPath?: string;
  // iterationBehavior?: 'once' | 'each';
  loopRadius?: number;
  branch?: 'true' | 'false';
  // Control point offset from default midpoint (for custom arrow curves)
  controlPointOffsetX?: number;
  controlPointOffsetY?: number;
}

// Union type for all block data types
export type DiagramNodeData = StartBlockData | PersonJobBlockData | JobBlockData | DBBlockData | ConditionBlockData | EndpointBlockData;

// Type for diagram nodes
export type DiagramNode = Node<DiagramNodeData>;

export interface DiagramState {
  // Person definitions shown in top bar, not as nodes
  persons: PersonDefinition[];
  nodes: DiagramNode[];
  arrows: Edge<ArrowData>[];
  apiKeys: ApiKey[];
}

export function applyArrowChanges(
  changes: EdgeChange[],
  arrows: Arrow[]
): Arrow[] {
  return applyEdgeChangesRF(changes, arrows);
}
export function addArrow<T = any>(
  arrow: Arrow | Connection,
  arrows: Arrow[]
): Arrow[] {
  return addEdgeRF(arrow, arrows);
}

export type ArrowChange = EdgeChange;
export type Arrow<T extends Record<string, unknown> = any> = Edge<T>;
export type OnArrowsChange = OnEdgesChange;

