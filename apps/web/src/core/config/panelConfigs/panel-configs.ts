import { arrowFields } from './arrow';
import { personFields } from './person';
import type { PanelLayoutConfig } from '@/features/diagram-editor/types/panel';

// Lazy initialization to avoid circular dependency issues
let _panelConfigs: Record<string, PanelLayoutConfig> | null = null;

export function getPanelConfigs(): Record<string, PanelLayoutConfig> {
  if (!_panelConfigs) {
    // Import FieldConverter only when needed to break circular dependency
    const { FieldConverter } = require('../field-registry');
    
    _panelConfigs = {
      arrow: {
        layout: 'single' as const,
        fields: arrowFields.map(field => FieldConverter.toPanelFieldConfig(field))
      } as PanelLayoutConfig,
      person: {
        layout: 'single' as const,
        fields: personFields.map(field => FieldConverter.toPanelFieldConfig(field))
      } as PanelLayoutConfig
    };
  }
  return _panelConfigs;
}

export const PANEL_CONFIGS = new Proxy({} as Record<string, PanelLayoutConfig>, {
  get(target, prop: string) {
    return getPanelConfigs()[prop];
  }
});