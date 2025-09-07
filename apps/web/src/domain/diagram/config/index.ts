/**
 * Export panel configurations for non-node entities
 */
export { ArrowPanelConfig, arrowFields } from './arrow';
export { PersonPanelConfig, personFields } from './person';

import { ArrowPanelConfig } from './arrow';
import { PersonPanelConfig } from './person';

/**
 * Panel configurations for non-node entities
 */
export const ENTITY_PANEL_CONFIGS = {
  arrow: ArrowPanelConfig,
  person: PersonPanelConfig
} as const;
