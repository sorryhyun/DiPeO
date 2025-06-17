import type { UserResponseFormData } from '@/features/diagram-editor/types/panel';
import { createUnifiedConfig } from '../unifiedConfig';

/**
 * Unified configuration for User Response node
 * This replaces both the node config and panel config
 */
export const userResponseConfig = createUnifiedConfig<UserResponseFormData>({
  // Node configuration
  label: 'User Response',
  icon: '❓',
  color: 'indigo',
  handles: {
    input: [{ id: 'default', position: 'left' }],
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { name: 'promptMessage', type: 'textarea', label: 'Prompt Message', required: true, placeholder: 'Enter message to display to user' },
    { name: 'timeoutSeconds', type: 'number', label: 'Timeout (seconds)', required: true, min: 1, max: 60 }
  ],
  defaults: { promptMessage: '', timeoutSeconds: 10, label: '', prompt: '', timeout: '10' },
  
  // Panel configuration overrides
  panelLayout: 'single',
  panelFieldOrder: ['label', 'prompt', 'timeout'],
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Node Name',
      placeholder: 'User Response'
    },
    {
      type: 'variableTextArea',
      name: 'prompt',
      label: 'Prompt Message',
      rows: 4,
      placeholder: 'Ask the user: {{variable}}',
      validate: (value) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'Prompt message is required' };
        }
        return { isValid: true };
      }
    },
    {
      type: 'text',
      name: 'timeout',
      label: 'Timeout (seconds)',
      placeholder: '10',
      validate: (value) => {
        const num = parseInt(value as string, 10);
        if (isNaN(num) || num < 1 || num > 60) {
          return { isValid: false, error: 'Timeout must be between 1 and 60 seconds' };
        }
        return { isValid: true };
      }
    }
  ]
});