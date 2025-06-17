import type { NodeKind } from '@/features/diagram-editor/types/node-kinds';
import { PANEL_CONFIGS } from './panelConfigs';
import { derivePanelConfig } from './unifiedConfig';
import { UNIFIED_NODE_CONFIGS } from './nodeConfigs';

export function getNodeConfig(type: NodeKind) {
  // Check if unified config exists
  const unifiedConfig = UNIFIED_NODE_CONFIGS[type];
  if (unifiedConfig) {
    // Extract node config properties from unified config
    const { panelLayout: _panelLayout, panelFieldOverrides: _panelFieldOverrides, panelFieldOrder: _panelFieldOrder, panelCustomFields: _panelCustomFields, ...nodeConfig } = unifiedConfig;
    return nodeConfig;
  }
  
  return UNIFIED_NODE_CONFIGS[type] || UNIFIED_NODE_CONFIGS.start;
}

export function validateNodeData(type: NodeKind, data: Record<string, any>) {
  const config = getNodeConfig(type);
  const errors: string[] = [];
  
  config.fields.forEach(field => {
    if (field.required && !data[field.name]) {
      errors.push(`${field.label} is required`);
    }
  });
  
  return { valid: errors.length === 0, errors };
}

export function getNodeDefaults(type: NodeKind) {
  return { ...getNodeConfig(type).defaults };
}

export function getNodeColorClasses(type: NodeKind) {
  const color = getNodeConfig(type).color;
  return {
    border: `border-${color}-500`,
    bg: `bg-${color}-50`,
    hover: `hover:bg-${color}-100`
  };
}

export function getPanelConfig(type: NodeKind | 'arrow' | 'person') {
  // Check if unified config exists for node types
  if (type !== 'arrow' && type !== 'person') {
    const unifiedConfig = UNIFIED_NODE_CONFIGS[type as NodeKind];
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