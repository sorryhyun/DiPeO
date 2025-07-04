import type { HookNodeData } from '@/features/diagram-editor/types/panel';
import { createUnifiedConfig } from '../unifiedConfig';

export const hookConfig = createUnifiedConfig<HookNodeData>({
  // Node configuration
  label: 'Hook',
  icon: '🪝',
  color: 'purple',
  handles: {
    input: [{ id: 'default', position: 'left' }],
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { 
      name: 'hook_type', 
      type: 'select', 
      label: 'Hook Type', 
      required: true,
      options: [
        { value: 'shell', label: 'Shell Command' },
        { value: 'webhook', label: 'Webhook' },
        { value: 'python', label: 'Python Script' },
        { value: 'file', label: 'File' }
      ]
    },
    { name: 'timeout', type: 'number', label: 'Timeout (seconds)', required: false, min: 1, max: 300 },
    { name: 'retry_count', type: 'number', label: 'Retry Count', required: false, min: 0, max: 10 },
    { name: 'retry_delay', type: 'number', label: 'Retry Delay (seconds)', required: false, min: 1, max: 60 }
  ],
  defaults: { 
    hook_type: 'shell',
    config: {},
    timeout: 30,
    retry_count: 0,
    retry_delay: 5
  },
  
  // Panel configuration overrides
  panelLayout: 'single',
  panelFieldOrder: ['label', 'hook_type', 'timeout', 'retry_count', 'retry_delay'],
  panelFieldOverrides: {
    hook_type: {
      placeholder: 'Select hook type'
    },
    timeout: {
      placeholder: '30'
    },
    retry_count: {
      placeholder: '0'
    },
    retry_delay: {
      placeholder: '5'
    }
  }
});