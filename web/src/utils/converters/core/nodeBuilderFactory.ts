/**
 * Node Builder Factory
 * 
 * Factory pattern for creating node builders with reduced duplication
 * and improved type safety.
 */

import { 
  generateNodeId,
  NodeKind,
  DomainNode,
  DomainHandle
} from '@/types';
import { generateNodeHandles, getDefaultHandles } from '@/utils/node';
import { getNodeConfig } from '@/config/helpers';
import type {
  NodeWithHandles,
  BaseNodeDataConfig,
  NodeBuilderConfig,
  NodeInfo,
  NodeBuilder
} from '../types';

// Re-export types for other modules
export type { NodeInfo, NodeBuilder, NodeWithHandles } from '../types';

// Common utilities
export const capitalize = (s: string) => s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

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

// Helper to add handles to a node
const addHandles = (node: DomainNode, nodeType: NodeKind): NodeWithHandles => {
  const nodeConfig = getNodeConfig(nodeType);
  const handles = nodeConfig 
    ? generateNodeHandles(node.id, nodeConfig, nodeType) 
    : getDefaultHandles(node.id, nodeType);
  return { 
    ...node, 
    handles
  };
};

/**
 * Factory function to create node builders
 */
export function createNodeBuilder<TData extends BaseNodeDataConfig = BaseNodeDataConfig>(
  config: NodeBuilderConfig<TData>
): NodeBuilder {
  return (info: NodeInfo): NodeWithHandles => {
    // Optional validation
    if (config.validate) {
      config.validate(info);
    }
    
    // Generate ID
    const id = generateNodeId();
    
    // Build base data
    let data = config.buildData(info, id);
    
    // Apply optional transformation
    if (config.transformData) {
      data = config.transformData(data, info);
    }
    
    // Create node
    const node: DomainNode = {
      id,
      type: config.nodeType,
      position: info.position,
      data,
      displayName: data.label || id
    };
    
    // Add handles and return
    return addHandles(node, config.nodeType);
  };
}

// Node builder configurations
export const NODE_BUILDER_CONFIGS = {
  start: {
    nodeType: 'start' as const,
    buildData: (info: NodeInfo, id: string) => ({
      id,
      label: capitalize(info.name),
      type: 'start'
    })
  },
  
  person_job: {
    nodeType: 'person_job' as const,
    buildData: (info: NodeInfo, id: string) => ({
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
    })
  },
  
  condition: {
    nodeType: 'condition' as const,
    buildData: (info: NodeInfo, id: string) => ({
      id,
      label: capitalize(info.name),
      type: 'condition',
      conditionType: info.conditionType || 'expression',
      expression: info.condition || info.expression || '',
      maxIterations: info.maxIterations
    })
  },
  
  db: {
    nodeType: 'db' as const,
    buildData: (info: NodeInfo, id: string) => ({
      id,
      label: capitalize(info.name),
      type: 'db',
      subType: info.subType || (info.dataSource?.match(/\.(txt|json|csv)$/) ? 'file' : 'fixed_prompt'),
      sourceDetails: info.dataSource || info.sourceDetails || ''
    })
  },
  
  job: {
    nodeType: 'job' as const,
    buildData: (info: NodeInfo, id: string) => ({
      id,
      label: capitalize(info.name),
      type: 'job',
      subType: info.subType || 'code',
      sourceDetails: info.code || info.sourceDetails || ''
    })
  },
  
  endpoint: {
    nodeType: 'endpoint' as const,
    buildData: (info: NodeInfo, id: string) => ({
      id,
      label: capitalize(info.name),
      type: 'endpoint',
      saveToFile: !!info.filePath,
      filePath: info.filePath || '',
      fileFormat: info.fileFormat || 'text'
    })
  },
  
  notion: {
    nodeType: 'notion' as const,
    buildData: (info: NodeInfo, id: string) => ({
      id,
      label: capitalize(info.name),
      type: 'notion',
      subType: info.subType || 'read',
      pageId: info.pageId || '',
      properties: info.properties || {}
    })
  },
  
  person_batch_job: {
    nodeType: 'person_batch_job' as const,
    buildData: (info: NodeInfo, id: string) => ({
      id,
      label: capitalize(info.name),
      type: 'person_batch_job',
      personId: info.personId,
      defaultPrompt: info.prompt || '',
      firstOnlyPrompt: info.firstPrompt || '',
      contextCleaningRule: info.contextCleaningRule || 'upon_request',
      mode: info.mode || 'sync',
      detectedVariables: detectVariables(info.prompt || '', info.firstPrompt || '')
    })
  },
  
  user_response: {
    nodeType: 'user_response' as const,
    buildData: (info: NodeInfo, id: string) => ({
      id,
      label: capitalize(info.name),
      type: 'user_response',
      promptMessage: info.promptMessage || 'Please provide input',
      timeoutSeconds: info.timeoutSeconds || 10
    })
  }
};

/**
 * Create all node builders using the factory
 */
export function createNodeBuilders(): Record<string, NodeBuilder> {
  const builders: Record<string, NodeBuilder> = {};
  
  // Create builders from configurations
  Object.entries(NODE_BUILDER_CONFIGS).forEach(([key, config]) => {
    builders[key] = createNodeBuilder(config);
  });
  
  // Add generic/fallback builder
  builders.generic = (info: NodeInfo) => {
    // Try to use person_job as fallback
    const fallbackBuilder = builders.person_job;
    if (fallbackBuilder) {
      return fallbackBuilder(info);
    }
    
    // Ultimate fallback - create a basic person_job node
    return createNodeBuilder({
      nodeType: 'person_job',
      buildData: (info: NodeInfo, id: string) => ({
        id,
        label: capitalize(info.name),
        type: 'person_job',
        personId: undefined,
        defaultPrompt: '',
        firstOnlyPrompt: '',
        contextCleaningRule: 'upon_request',
        maxIterations: 1,
        mode: 'sync',
        detectedVariables: []
      })
    })(info);
  };
  
  return builders;
}

/**
 * Advanced factory features
 */

// Create a builder with validation
export function createValidatedNodeBuilder<TData extends BaseNodeDataConfig>(
  config: NodeBuilderConfig<TData>,
  validator: (info: NodeInfo) => void
): NodeBuilder {
  return createNodeBuilder({
    ...config,
    validate: validator
  });
}

// Create a builder with data transformation
export function createTransformedNodeBuilder<TData extends BaseNodeDataConfig>(
  config: NodeBuilderConfig<TData>,
  transformer: (data: TData, info: NodeInfo) => TData
): NodeBuilder {
  return createNodeBuilder({
    ...config,
    transformData: transformer
  });
}

// Create a builder that inherits from another
export function createExtendedNodeBuilder<TData extends BaseNodeDataConfig>(
  baseConfig: NodeBuilderConfig<TData>,
  extensions: Partial<NodeBuilderConfig<TData>>
): NodeBuilder {
  return createNodeBuilder({
    ...baseConfig,
    ...extensions,
    buildData: extensions.buildData || baseConfig.buildData,
    transformData: (data, info) => {
      let result = data;
      if (baseConfig.transformData) {
        result = baseConfig.transformData(result, info);
      }
      if (extensions.transformData) {
        result = extensions.transformData(result, info);
      }
      return result;
    },
    validate: (info) => {
      if (baseConfig.validate) baseConfig.validate(info);
      if (extensions.validate) extensions.validate(info);
    }
  });
}

// Utility to register a new node type dynamically
export function registerNodeBuilder(
  builders: Record<string, NodeBuilder>,
  nodeType: string,
  config: NodeBuilderConfig
): void {
  builders[nodeType] = createNodeBuilder(config);
}