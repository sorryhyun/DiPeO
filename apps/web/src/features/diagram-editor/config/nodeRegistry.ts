import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { NodeType } from '@dipeo/domain-models';
import { NODE_CONFIGS_MAP } from './nodes';

/**
 * Dynamic node registry for registering node configurations at runtime
 * This complements the static NODE_CONFIGS_MAP for diagram-generated nodes
 */
const dynamicNodeConfigs: Map<string, UnifiedNodeConfig<any>> = new Map();

/**
 * Register a node configuration dynamically
 * Used by diagram-generated node configurations
 */
export function registerNodeConfig(config: UnifiedNodeConfig<any>): void {
  if (!config.nodeType) {
    console.error('Cannot register node config without nodeType:', config);
    return;
  }
  
  dynamicNodeConfigs.set(config.nodeType, config);
}

/**
 * Get all registered node configurations
 * Merges static and dynamic configurations
 */
export function getAllNodeConfigs(): Map<string, UnifiedNodeConfig<any>> {
  const allConfigs = new Map<string, UnifiedNodeConfig<any>>();
  
  // First add static configs
  Object.entries(NODE_CONFIGS_MAP).forEach(([nodeType, config]) => {
    allConfigs.set(nodeType, config);
  });
  
  // Then add/override with dynamic configs
  dynamicNodeConfigs.forEach((config, nodeType) => {
    allConfigs.set(nodeType, config);
  });
  
  return allConfigs;
}

/**
 * Get a specific node configuration by type
 * Checks dynamic registry first, then falls back to static
 */
export function getNodeConfig(nodeType: string | NodeType): UnifiedNodeConfig<any> | undefined {
  // Check dynamic configs first
  const dynamicConfig = dynamicNodeConfigs.get(nodeType);
  if (dynamicConfig) {
    return dynamicConfig;
  }
  
  // Fall back to static configs
  return NODE_CONFIGS_MAP[nodeType as NodeType];
}

/**
 * Get a specific node configuration by type (legacy function name)
 */
export function getDynamicNodeConfig(nodeType: string): UnifiedNodeConfig<any> | undefined {
  return dynamicNodeConfigs.get(nodeType);
}

/**
 * Clear all dynamically registered node configurations
 * Useful for testing or resetting state
 */
export function clearDynamicNodeConfigs(): void {
  dynamicNodeConfigs.clear();
}