import { HandleLabel } from '@dipeo/domain-models';
import type { UserResponseNodeData } from '@/core/types';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the User Response node type
 * Combines visual metadata, node structure, and field definitions
 */
export const UserResponseNodeConfig: UnifiedNodeConfig<UserResponseNodeData> = {
  // Visual metadata
  label: 'User Response',
  icon: '💬',
  color: '#14b8a6',
  nodeType: 'user_response' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
    output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
  },
  
  // Default values
  defaults: { 
    label: 'User Response', 
    prompt: '' 
  },
  
  // Panel layout configuration
  panelLayout: 'single',
  panelFieldOrder: ['label', 'prompt', 'timeout'],
  
  // Field definitions
  customFields: [
    {
      name: 'label',
      type: 'text',
      label: 'Label',
      required: true,
      placeholder: 'Enter user response label'
    },
    {
      name: 'prompt',
      type: 'variableTextArea',
      label: 'Prompt for User',
      required: true,
      placeholder: 'What would you like to ask the user?',
      rows: 3,
      showPromptFileButton: true,
      validate: (value: unknown) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'Prompt is required' };
        }
        return { isValid: true };
      }
    },
    {
      name: 'timeout',
      type: 'number',
      label: 'Timeout (seconds)',
      placeholder: 'Optional timeout in seconds',
      min: 1
    }
  ]
};