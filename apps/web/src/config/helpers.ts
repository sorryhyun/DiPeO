import type { NodeType } from '@/types';
import { NODE_CONFIGS } from './nodeConfigs';
import { PANEL_CONFIGS } from './panelConfigs';

export function getNodeConfig(type: NodeType) {
  return NODE_CONFIGS[type] || NODE_CONFIGS.start;
}

export function validateNodeData(type: NodeType, data: Record<string, any>) {
  const config = getNodeConfig(type);
  const errors: string[] = [];
  
  config.fields.forEach(field => {
    if (field.required && !data[field.name]) {
      errors.push(`${field.label} is required`);
    }
  });
  
  return { valid: errors.length === 0, errors };
}

export function getNodeDefaults(type: NodeType) {
  return { ...getNodeConfig(type).defaults };
}

export function getNodeColorClasses(type: NodeType) {
  const color = getNodeConfig(type).color;
  return {
    border: `border-${color}-500`,
    bg: `bg-${color}-50`,
    hover: `hover:bg-${color}-100`
  };
}

export function getPanelConfig(type: NodeType | 'arrow' | 'person') {
  return PANEL_CONFIGS[type] || null;
}