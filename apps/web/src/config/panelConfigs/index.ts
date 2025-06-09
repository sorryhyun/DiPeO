import { arrowPanelConfig } from './arrow';
import { personPanelConfig } from './person';

// Only keep arrow and person configs as they are not node types
export const PANEL_CONFIGS = {
  arrow: arrowPanelConfig,
  person: personPanelConfig
};

export * from './arrow';
export * from './person';