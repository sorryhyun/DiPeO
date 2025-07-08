import { HandleLabel } from '@dipeo/domain-models';
import type { HookNodeData } from '@/core/types';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the Hook node type
 * Combines visual metadata, node structure, and field definitions
 */
export const HookNodeConfig: UnifiedNodeConfig<HookNodeData> = {
  // Visual metadata
  label: 'Hook',
  icon: '🪝',
  color: '#9333ea',
  nodeType: 'hook' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
    output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
  },
  
  // Default values
  defaults: { 
    label: 'Hook', 
    hook_type: 'webhook', 
    command: '' 
  },
  
  // Panel layout configuration
  panelLayout: 'single',
  panelFieldOrder: ['label', 'event', 'custom_event', 'action'],
  
  // Field definitions
  customFields: [
    {
      name: 'label',
      type: 'text',
      label: 'Label',
      required: true,
      placeholder: 'Enter hook label'
    },
    {
      name: 'event',
      type: 'select',
      label: 'Event Type',
      required: true,
      options: [
        { value: 'on_start', label: 'On Start' },
        { value: 'on_complete', label: 'On Complete' },
        { value: 'on_error', label: 'On Error' },
        { value: 'custom', label: 'Custom Event' }
      ]
    },
    {
      name: 'custom_event',
      type: 'text',
      label: 'Custom Event Name',
      placeholder: 'Enter custom event name',
      conditional: {
        field: 'event',
        values: ['custom']
      }
    },
    {
      name: 'action',
      type: 'variableTextArea',
      label: 'Action',
      required: true,
      placeholder: 'Define the hook action',
      rows: 5
    }
  ]
};