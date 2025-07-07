import { NodeType } from '@dipeo/domain-models';
import { derivePanelConfig } from './unifiedConfig';
import type { NodeTypeKey } from '@/core/types/type-factories';
import { NODE_REGISTRY, createNodeConfigFromRegistry } from './node-registry';
import { PANEL_CONFIGS } from './panelConfigs/index';

// Create unified configs on demand to avoid circular dependency
function getUnifiedNodeConfig(type: NodeType) {
  const entry = NODE_REGISTRY[type];
  if (!entry) return null;
  return createNodeConfigFromRegistry(type as NodeTypeKey, entry);
}

export function getNodeConfig(type: NodeType) {
  // Check if unified config exists
  const unifiedConfig = getUnifiedNodeConfig(type);
  if (unifiedConfig) {
    // Extract node config properties from unified config
    const { panelLayout: _panelLayout, panelFieldOverrides: _panelFieldOverrides, panelFieldOrder: _panelFieldOrder, panelCustomFields: _panelCustomFields, ...nodeConfig } = unifiedConfig;
    return nodeConfig;
  }
  
  // Fallback to start node config
  const startConfig = getUnifiedNodeConfig(NodeType.START);
  const { panelLayout: _panelLayout, panelFieldOverrides: _panelFieldOverrides, panelFieldOrder: _panelFieldOrder, panelCustomFields: _panelCustomFields, ...startNodeConfig } = startConfig!;
  return startNodeConfig;
}


export function getNodeDefaults(type: NodeType) {
  return { ...getNodeConfig(type).defaults };
}


export function getPanelConfig(type: NodeType | 'arrow' | 'person') {
  // Check if unified config exists for node types
  if (type !== 'arrow' && type !== 'person') {
    const unifiedConfig = getUnifiedNodeConfig(type as NodeType);
    if (unifiedConfig) {
      return derivePanelConfig(unifiedConfig);
    }
  }
  
  // Only arrow and person remain in PANEL_CONFIGS
  if (type === 'arrow' || type === 'person') {
    return PANEL_CONFIGS[type];
  }
  
  return null;
}