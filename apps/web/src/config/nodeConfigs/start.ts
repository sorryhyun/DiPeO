import type { StartFormData } from '@/types/ui';
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
  panelLayout: 'single',
  panelFieldOrder: ['label'],
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'Start',
      validate: (_value) => ({
        isValid: true // Label is optional
      })
    }
  ]
});