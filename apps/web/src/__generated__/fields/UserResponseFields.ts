// Generated field configuration for user_response
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const userResponseFields: UnifiedFieldDefinition[] = [
  {
    name: 'prompt',
    type: 'text',
    label: '"Prompt"',
    required: true,
    placeholder: '"Enter prompt template..."',
    description: '"Question to ask the user"',
  },
  {
    name: 'timeout',
    type: 'text',
    label: '"Timeout"',
    required: false,
    defaultValue: 300,
    description: '"Response timeout in seconds"',
    min: 0,
    max: 3600,
  },
];
