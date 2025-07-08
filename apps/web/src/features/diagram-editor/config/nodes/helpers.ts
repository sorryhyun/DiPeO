import { NodeType } from '@dipeo/domain-models';
import { derivePanelConfig } from '@/core/config/unifiedConfig';
import { ENTITY_PANEL_CONFIGS } from '@/features/properties-editor/config';
import { NODE_CONFIGS_MAP } from './index';

/**
 * Get node defaults for a given node type
 */
export function getNodeDefaults(type: NodeType) {
  const config = NODE_CONFIGS_MAP[type];
  return config ? { ...config.defaults } : {};
}

/**
 * Get panel configuration for a given entity type
 */
export function getPanelConfig(type: NodeType | 'arrow' | 'person') {
  // Check if unified config exists for node types
  if (type !== 'arrow' && type !== 'person') {
    const unifiedConfig = NODE_CONFIGS_MAP[type as NodeType];
    if (unifiedConfig) {
      return derivePanelConfig(unifiedConfig);
    }
  }
  
  // Only arrow and person remain in ENTITY_PANEL_CONFIGS
  if (type === 'arrow' || type === 'person') {
    return ENTITY_PANEL_CONFIGS[type];
  }
  
  return null;
}