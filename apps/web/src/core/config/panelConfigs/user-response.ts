import type { UnifiedFieldDefinition } from '../field-registry';
import type { UserResponseNodeData } from '@/core/types';

export const userResponseFields: UnifiedFieldDefinition<UserResponseNodeData>[] = [
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
    showPromptFileButton: true
  },
  {
    name: 'timeout',
    type: 'number',
    label: 'Timeout (seconds)',
    placeholder: 'Optional timeout in seconds',
    min: 1
  }
];