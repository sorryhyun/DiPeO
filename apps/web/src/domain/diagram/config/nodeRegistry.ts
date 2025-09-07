import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType } from '@dipeo/models';

/**
 * Dynamic node registry for registering node configurations at runtime
 * This is the primary registry for all node configurations
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

  // Ensure we store using the string value
  const nodeTypeStr = typeof config.nodeType === 'string' ? config.nodeType : String(config.nodeType);
  dynamicNodeConfigs.set(nodeTypeStr, config);
}

/**
 * Get all registered node configurations
 */
export function getAllNodeConfigs(): Map<string, UnifiedNodeConfig<any>> {
  return new Map(dynamicNodeConfigs);
}

/**
 * Get a specific node configuration by type
 */
export function getNodeConfig(nodeType: string | NodeType): UnifiedNodeConfig<any> | undefined {
  return dynamicNodeConfigs.get(nodeType as string);
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
