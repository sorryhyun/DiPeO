// Consolidated type exports
export * from './core';
export * from './runtime';
export * from './ui';

// Import node configs - needs to be here to avoid circular deps
import { PanelConfig } from './ui';
import {
  startConfig,
  endpointConfig,
  personJobConfig,
  conditionConfig,
  dbConfig,
  jobConfig,
  personBatchJobConfig,
  arrowConfig,
  personConfig,
  userResponseConfig,
  notionConfig
} from '../features/properties/configs';

export interface UnifiedNodeConfig {
  nodeType: string;
  reactFlowType: string;
  config: PanelConfig<Record<string, any>>;
}

export const UNIFIED_NODE_CONFIGS: Record<string, UnifiedNodeConfig> = {
  start: {
    nodeType: 'start',
    reactFlowType: 'start',
    config: startConfig
  },
  endpoint: {
    nodeType: 'endpoint',
    reactFlowType: 'endpoint',
    config: endpointConfig
  },
  person_job: {
    nodeType: 'person_job',
    reactFlowType: 'person_job',
    config: personJobConfig
  },
  condition: {
    nodeType: 'condition',
    reactFlowType: 'condition',
    config: conditionConfig
  },
  db: {
    nodeType: 'db',
    reactFlowType: 'db',
    config: dbConfig
  },
  job: {
    nodeType: 'job',
    reactFlowType: 'job',
    config: jobConfig
  },
  person_batch_job: {
    nodeType: 'person_batch_job',
    reactFlowType: 'person_batch_job',
    config: personBatchJobConfig
  },
  user_response: {
    nodeType: 'user_response',
    reactFlowType: 'user_response',
    config: userResponseConfig
  },
  notion: {
    nodeType: 'notion',
    reactFlowType: 'notion',
    config: notionConfig
  },
  person: {
    nodeType: 'person',
    reactFlowType: 'person',
    config: personConfig
  }
};

// Export individual node configs for convenience
export const getNodeConfig = (nodeType: string): PanelConfig<Record<string, any>> | undefined => {
  return UNIFIED_NODE_CONFIGS[nodeType]?.config;
};

// Export React Flow type mapping
export const getReactFlowType = (nodeType: string): string | undefined => {
  return UNIFIED_NODE_CONFIGS[nodeType]?.reactFlowType;
};