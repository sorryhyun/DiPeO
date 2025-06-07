import { nanoid } from 'nanoid';
import { Node, NodeType } from '@/types';

// Common utilities
export const capitalize = (s: string) => s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

// Node info type for builder input
export interface NodeInfo {
  name: string;
  type: NodeType | 'generic';
  position: { x: number; y: number };
  hasPrompt?: boolean;
  hasAgent?: boolean;
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

// Type for node builder functions
type NodeBuilder<T extends Node = Node> = (info: NodeInfo) => T;

// Unified node builders lookup map
export const NODE_BUILDERS: Record<string, NodeBuilder> = {
  start: (info) => {
    const id = `st-${nanoid(4)}`;
    return {
      id,
      type: 'start' as const,
      position: info.position,
      data: {
        id,
        label: capitalize(info.name),
        type: 'start'
      }
    };
  },

  person_job: (info) => ({
    id: `pj-${nanoid(4)}`,
    type: 'person_job',
    position: info.position,
    data: {
      id: `pj-${nanoid(4)}`,
      label: capitalize(info.name),
      type: 'person_job',
      personId: info.personId,
      defaultPrompt: info.prompt || '',
      firstOnlyPrompt: info.firstPrompt || '',
      contextCleaningRule: info.contextCleaningRule || 'upon_request',
      maxIterations: info.maxIterations || 1,
      mode: info.mode || 'sync',
      detectedVariables: detectVariables(info.prompt || '', info.firstPrompt || '')
    }
  }),

  condition: (info) => ({
    id: `cd-${nanoid(4)}`,
    type: 'condition',
    position: info.position,
    data: {
      id: `cd-${nanoid(4)}`,
      label: capitalize(info.name),
      type: 'condition',
      conditionType: info.conditionType || 'expression',
      expression: info.condition || info.expression || '',
      maxIterations: info.maxIterations
    }
  }),

  db: (info) => ({
    id: `db-${nanoid(4)}`,
    type: 'db',
    position: info.position,
    data: {
      id: `db-${nanoid(4)}`,
      label: capitalize(info.name),
      type: 'db',
      subType: info.subType || (info.dataSource?.match(/\.(txt|json|csv)$/) ? 'file' : 'fixed_prompt'),
      sourceDetails: info.dataSource || info.sourceDetails || ''
    }
  }),

  job: (info) => ({
    id: `jb-${nanoid(4)}`,
    type: 'job',
    position: info.position,
    data: {
      id: `jb-${nanoid(4)}`,
      label: capitalize(info.name),
      type: 'job',
      subType: info.subType || 'code',
      sourceDetails: info.code || info.sourceDetails || ''
    }
  }),

  endpoint: (info) => ({
    id: `ep-${nanoid(4)}`,
    type: 'endpoint',
    position: info.position,
    data: {
      id: `ep-${nanoid(4)}`,
      label: capitalize(info.name),
      type: 'endpoint',
      saveToFile: !!info.filePath,
      filePath: info.filePath || '',
      fileFormat: info.fileFormat || 'text'
    }
  }),

  notion: (info) => ({
    id: `nt-${nanoid(4)}`,
    type: 'notion',
    position: info.position,
    data: {
      id: `nt-${nanoid(4)}`,
      label: capitalize(info.name),
      type: 'notion',
      subType: info.subType || 'read',
      pageId: info.pageId || '',
      properties: info.properties || {}
    }
  }),

  person_batch_job: (info) => ({
    id: `pb-${nanoid(4)}`,
    type: 'person_batch_job',
    position: info.position,
    data: {
      id: `pb-${nanoid(4)}`,
      label: capitalize(info.name),
      type: 'person_batch_job',
      personId: info.personId,
      defaultPrompt: info.prompt || '',
      firstOnlyPrompt: info.firstPrompt || '',
      contextCleaningRule: info.contextCleaningRule || 'upon_request',
      mode: info.mode || 'sync',
      detectedVariables: detectVariables(info.prompt || '', info.firstPrompt || '')
    }
  }),

  user_response: (info) => ({
    id: `ur-${nanoid(4)}`,
    type: 'user_response',
    position: info.position,
    data: {
      id: `ur-${nanoid(4)}`,
      label: capitalize(info.name),
      type: 'user_response',
      promptMessage: info.promptMessage || 'Please provide input',
      timeoutSeconds: info.timeoutSeconds || 10
    }
  }),

  // Generic fallback
  generic: (info) => {
    const personJobBuilder = NODE_BUILDERS.person_job;
    if (personJobBuilder) {
      return personJobBuilder(info);
    }
    // Ultimate fallback
    return {
      id: `nd-${nanoid(4)}`,
      type: 'person_job' as const,
      position: info.position,
      data: {
        id: `nd-${nanoid(4)}`,
        label: capitalize(info.name),
        type: 'person_job',
        defaultPrompt: '',
        firstOnlyPrompt: '',
        contextCleaningRule: 'upon_request',
        maxIterations: 1,
        mode: 'sync',
        detectedVariables: []
      }
    };
  }
};

/**
 * Build a node using the unified builder system
 */
export function buildNode(info: NodeInfo): Node {
  const nodeType = info.type || 'generic';
  const builder = NODE_BUILDERS[nodeType] || NODE_BUILDERS.generic;
  if (!builder) {
    throw new Error(`No builder found for node type: ${nodeType}`);
  }
  return builder(info);
}

/**
 * Build multiple nodes from a record of node infos
 */
export function buildNodes(nodeInfos: Record<string, NodeInfo>): Node[] {
  return Object.values(nodeInfos).map(info => buildNode(info));
}

/**
 * Detect variables in prompts
 */
export function detectVariables(...prompts: string[]): string[] {
  const vars = new Set<string>();
  const varPattern = /{{(\w+)}}/g;
  
  prompts.forEach(prompt => {
    if (prompt) {
      const matches = prompt.matchAll(varPattern);
      for (const match of matches) {
        vars.add(match[1] || '');
      }
    }
  });
  
  return Array.from(vars);
}

/**
 * Get node type prefix for ID generation
 */
export function getNodeTypePrefix(nodeType: string): string {
  const prefixMap: Record<string, string> = {
    start: 'st',
    person_job: 'pj',
    condition: 'cd',
    db: 'db',
    job: 'jb',
    endpoint: 'ep',
    notion: 'nt',
    person_batch_job: 'pb',
    user_response: 'ur'
  };
  return prefixMap[nodeType] || 'nd';
}