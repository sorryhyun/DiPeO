import { HandleLabel } from '@dipeo/domain-models';
import type { StartNodeData } from '@/core/types';
import { createNodeConfig } from './createNodeConfig';

/**
 * Complete configuration for the Start node type
 * Combines visual metadata, node structure, and field definitions
 * Field configurations are automatically generated from domain models
 */
export const StartNodeConfig = createNodeConfig<StartNodeData>({
  // Visual metadata
  nodeType: 'start' as any,
  label: 'Start',
  icon: '🚀',
  color: '#10b981',
  
  // Node structure
  handles: {
    output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
  },
  
  // Default values
  defaults: { 
    label: 'Start',
    custom_data: {},
    output_data_structure: {},
    trigger_mode: 'manual'
  },
  
  // Panel layout configuration
  panelLayout: 'twoColumn'
});