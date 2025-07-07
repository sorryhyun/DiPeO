// Main export file that maintains the existing API
import type { NodeType } from '@dipeo/domain-models';
import { NODE_REGISTRY, createNodeConfigFromRegistry } from './node-registry';
import type { UnifiedNodeConfig } from './unifiedConfig';
import type { NodeTypeKey } from '@/core/types/type-factories';

export * from './helpers';
export { PANEL_CONFIGS } from './panelConfigs';
export * from './unifiedConfig';
export * from './node-registry';
export * from './field-registry';

// Create UNIFIED_NODE_CONFIGS from the registry for backward compatibility
export const UNIFIED_NODE_CONFIGS: Record<NodeType, UnifiedNodeConfig<Record<string, unknown>>> = 
  Object.fromEntries(
    Object.entries(NODE_REGISTRY).map(([nodeType, entry]) => [
      nodeType,
      createNodeConfigFromRegistry(nodeType as NodeTypeKey, entry)
    ])
  ) as Record<NodeType, UnifiedNodeConfig<Record<string, unknown>>>;

// Re-export individual configs if needed
export * from './panelConfigs';