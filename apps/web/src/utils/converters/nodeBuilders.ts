import { generateShortId } from '@/types/primitives/id-generation';
import type { DomainNode, DomainHandle } from '@/types/domain';
import type { NodeWithHandles } from './diagramAssembler';
import { NodeKind } from '@/types/primitives/enums';
import { nodeId, NodeID } from '@/types/branded';
import { generateNodeHandles, getDefaultHandles } from '@/utils/node';
import { getNodeConfig } from '@/config/helpers';

// Common utilities
export const capitalize = (s: string) => s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

// Helper to add handles to a node
const addHandles = (node: DomainNode, nodeType: NodeKind): NodeWithHandles => {
  const nodeConfig = getNodeConfig(nodeType);
  const handles = nodeConfig 
    ? generateNodeHandles(node.id, nodeConfig, nodeType) 
    : getDefaultHandles(node.id, nodeType);
  return { 
    ...node, 
    handles,
    // Add ReactFlow required properties
    draggable: true,
    selectable: true,
    connectable: true
  } as NodeWithHandles;
};

// Node info type for builder input
export interface NodeInfo {
  name: string;
  type: NodeKind | 'generic';
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
type NodeBuilder = (info: NodeInfo) => NodeWithHandles;

// Unified node builders lookup map
export const NODE_BUILDERS: Record<string, NodeBuilder> = {
  start: (info) => {
    const id = nodeId(`st-${generateShortId()}`);
    return addHandles({
      id,
      type: 'start' as const,
      position: info.position,
      data: {
        id,
        label: capitalize(info.name),
        type: 'start'
      }
    }, 'start');
  },

  person_job: (info) => {
    const id = nodeId(`pj-${generateShortId()}`);
    return addHandles({
      id,
      type: 'person_job',
      position: info.position,
      data: {
        id,
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
    }, 'person_job');
  },

  condition: (info) => {
    const id = nodeId(`cd-${generateShortId()}`);
    return addHandles({
      id,
      type: 'condition' as const,
      position: info.position,
      data: {
        id,
        label: capitalize(info.name),
        type: 'condition',
        conditionType: info.conditionType || 'expression',
        expression: info.condition || info.expression || '',
        maxIterations: info.maxIterations
      }
    }, 'condition');
  },

  db: (info) => {
    const id = nodeId(`db-${generateShortId()}`);
    return addHandles({
      id,
      type: 'db' as const,
      position: info.position,
      data: {
        id,
        label: capitalize(info.name),
        type: 'db',
        subType: info.subType || (info.dataSource?.match(/\.(txt|json|csv)$/) ? 'file' : 'fixed_prompt'),
        sourceDetails: info.dataSource || info.sourceDetails || ''
      }
    }, 'db');
  },

  job: (info) => {
    const id = nodeId(`jb-${generateShortId()}`);
    return addHandles({
      id,
      type: 'job' as const,
      position: info.position,
      data: {
        id,
        label: capitalize(info.name),
        type: 'job',
        subType: info.subType || 'code',
        sourceDetails: info.code || info.sourceDetails || ''
      }
    }, 'job');
  },

  endpoint: (info) => {
    const id = nodeId(`ep-${generateShortId()}`);
    return addHandles({
      id,
      type: 'endpoint' as const,
      position: info.position,
      data: {
        id,
        label: capitalize(info.name),
        type: 'endpoint',
        saveToFile: !!info.filePath,
        filePath: info.filePath || '',
        fileFormat: info.fileFormat || 'text'
      }
    }, 'endpoint');
  },

  notion: (info) => {
    const id = nodeId(`nt-${generateShortId()}`);
    return addHandles({
      id,
      type: 'notion' as const,
      position: info.position,
      data: {
        id,
        label: capitalize(info.name),
        type: 'notion',
        subType: info.subType || 'read',
        pageId: info.pageId || '',
        properties: info.properties || {}
      }
    }, 'notion');
  },

  person_batch_job: (info) => {
    const id = nodeId(`pb-${generateShortId()}`);
    return addHandles({
      id,
      type: 'person_batch_job' as const,
      position: info.position,
      data: {
        id,
        label: capitalize(info.name),
        type: 'person_batch_job',
        personId: info.personId,
        defaultPrompt: info.prompt || '',
        firstOnlyPrompt: info.firstPrompt || '',
        contextCleaningRule: info.contextCleaningRule || 'upon_request',
        mode: info.mode || 'sync',
        detectedVariables: detectVariables(info.prompt || '', info.firstPrompt || '')
      }
    }, 'person_batch_job');
  },

  user_response: (info) => {
    const id = nodeId(`ur-${generateShortId()}`);
    return addHandles({
      id,
      type: 'user_response' as const,
      position: info.position,
      data: {
        id,
        label: capitalize(info.name),
        type: 'user_response',
        promptMessage: info.promptMessage || 'Please provide input',
        timeoutSeconds: info.timeoutSeconds || 10
      }
    }, 'user_response');
  },

  // Generic fallback
  generic: (info) => {
    const personJobBuilder = NODE_BUILDERS.person_job;
    if (personJobBuilder) {
      return personJobBuilder(info);
    }
    // Ultimate fallback
    const id = nodeId(`nd-${generateShortId()}`);
    return addHandles({
      id,
      type: 'person_job' as const,
      position: info.position,
      data: {
        id,
        label: capitalize(info.name),
        type: 'person_job',
        defaultPrompt: '',
        firstOnlyPrompt: '',
        contextCleaningRule: 'upon_request',
        maxIterations: 1,
        mode: 'sync',
        detectedVariables: []
      }
    }, 'person_job');
  }
};

/**
 * Build a node using the unified builder system
 */
export function buildNode(info: NodeInfo): NodeWithHandles {
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
export function buildNodes(nodeInfos: Record<string, NodeInfo>): DomainNode[] {
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