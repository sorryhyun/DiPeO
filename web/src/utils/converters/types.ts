// Shared types and interfaces for converter modules

import type { 
  DomainNode, 
  DomainArrow, 
  DomainPerson, 
  DomainApiKey, 
  DomainHandle,
  NodeKind 
} from '@/types';

// Graph representation types
export interface Edge {
  source: string;
  target: string;
  condition: string | null;
  variable: string | null;
}

export interface NodeAnalysis {
  name: string;
  type: string;
  incoming: Edge[];
  outgoing: Edge[];
  [key: string]: any;
}

export interface NodePosition {
  x: number;
  y: number;
}

// Node builder types
export interface NodeWithHandles extends DomainNode {
  handles: DomainHandle[];
}

export interface NodeInfo {
  name: string;
  type: NodeKind | 'generic';
  position: { x: number; y: number };
  hasPrompt?: boolean;
  hasPerson?: boolean;
  prompt?: string;
  firstPrompt?: string;
  condition?: string;
  dataSource?: string;
  code?: string;
  filePath?: string;
  fileFormat?: string;
  personId?: string;
  [key: string]: any;
}

export type NodeBuilder = (info: NodeInfo) => NodeWithHandles;

// Node builder configuration types
export interface BaseNodeDataConfig extends Record<string, unknown> {
  label: string;
  type: string;
}

export interface NodeBuilderConfig<TData extends BaseNodeDataConfig = BaseNodeDataConfig> {
  nodeType: NodeKind;
  buildData: (info: NodeInfo, id: string) => TData;
  transformData?: (data: TData, info: NodeInfo) => TData;
  validate?: (info: NodeInfo) => void;
}

// Callback interfaces for diagram assembly
export interface AssemblerCallbacks {
  parseFlow: (flowData: any) => Edge[];
  inferNodeType: (name: string, context: any) => string;
  createNodeInfo: (name: string, analysis: NodeAnalysis, context: any) => any;
  createArrowData: (edge: Edge, sourceId: string, targetId: string) => any;
  extractPersons: (nodeAnalysis: Record<string, NodeAnalysis>, context: any) => DomainPerson[];
  extractApiKeys: (persons: DomainPerson[]) => DomainApiKey[];
  linkPersonsToNodes?: (nodes: DomainNode[], nodeAnalysis: Record<string, NodeAnalysis>, context: any) => void;
}

export interface AssemblerOptions {
  source: any;
  callbacks: AssemblerCallbacks;
}

// YAML format types
export interface YamlDiagram {
  version: '1.0';
  title?: string;
  metadata?: {
    description?: string;
  };
  apiKeys: Record<string, {
    service: string;
    name: string;
  }>;
  persons: Record<string, {
    model: string;
    service: string;
    apiKeyLabel?: string;
    system?: string;
    temperature?: number;
  }>;
  workflow: {
    label: string;
    type: string;
    position: { x: number; y: number };
    person?: string;
    prompt?: string;
    first_prompt?: string;
    source?: string;
    code?: string;
    expression?: string;
    file?: string;
    file_format?: string;
    forget?: string;
    max_iterations?: number;
    mode?: string;
    condition_type?: string;
    sub_type?: string;
    connections?: {
      to: string;
      label?: string;
      content_type?: string;
      branch?: string;
      source_handle?: string;
      target_handle?: string;
      control_offset?: { x: number; y: number };
    }[];
  }[];
}

// LLM-YAML format types
export interface LLMYamlFormat {
  flow: Record<string, string | string[]> | string[];
  prompts?: Record<string, string>;
  persons?: Record<string, string | {
    model?: string;
    service?: string;
    system?: string;
    temperature?: number;
  }>;
  data?: Record<string, string>;
}