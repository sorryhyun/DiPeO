import React from 'react';
import { Panel } from '../wrappers';
import { PANEL_CONFIGS } from '../utils/panelConfig';
import type { ArrowData, PersonDefinition } from '@repo/core-model';

// Re-export the UniversalPropertiesPanel from its own file
export { UniversalPropertiesPanel } from './UniversalPropertiesPanel';

// Keep only the panels that are still in use
export const ArrowPropertiesPanel: React.FC<{ arrowId: string; data: ArrowData }> = (props) => (
  <Panel {...PANEL_CONFIGS.arrow}>{PANEL_CONFIGS.arrow.render(props)}</Panel>
);

export const PersonPropertiesPanel: React.FC<{ personId: string; data: PersonDefinition }> = (props) => (
  <Panel {...PANEL_CONFIGS.person}>{PANEL_CONFIGS.person.render(props)}</Panel>
);