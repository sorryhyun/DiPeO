import type { StartFormData } from '@/features/diagram-editor/types/panel';
import { createUnifiedConfig } from '../unifiedConfig';

/**
 * Unified configuration for Start node
 * This replaces both the node config and panel config
 */
export const startConfig = createUnifiedConfig<StartFormData>({
  // Node configuration
  label: 'Start',
  icon: '🚀',
  color: 'green',
  handles: {
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { name: 'output', type: 'textarea', label: 'Output Data', required: true, placeholder: 'Enter static data to output' }
  ],
  defaults: { output: '', label: '' },
  
  // Panel configuration overrides
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'output'],
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'Start',
      column: 1,
      validate: (_value) => ({
        isValid: true // Label is optional
      })
    },
    {
      type: 'textarea',
      name: 'output',
      label: 'Output Data',
      placeholder: 'Enter static data to output',
      column: 2,
      rows: 3,
      validate: (value) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'Output data is required' };
        }
        return { isValid: true };
      }
    }
  ]
});