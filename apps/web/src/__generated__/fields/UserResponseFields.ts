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
    adjustable: true,
  },
  {
    name: 'timeout',
    type: 'text',
    label: '"Timeout"',
    required: false,
    description: '"Response timeout in seconds"',
    min: 0,
    max: 3600,
    validate: (value: unknown) => {
      if (typeof value === 'number' && value < 0) {
        return { isValid: false, error: 'Value must be at least 0' };
      }
      if (typeof value === 'number' && value > 3600) {
        return { isValid: false, error: 'Value must be at most 3600' };
      }
      return { isValid: true };
    },
  },
];
