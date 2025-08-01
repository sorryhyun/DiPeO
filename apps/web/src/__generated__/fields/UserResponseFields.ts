// Generated field configuration for user_response
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const userResponseFields: UnifiedFieldDefinition[] = [
  {
    name: 'prompt',
    type: 'textarea',
    label: 'Prompt',
    required: true,
    placeholder: 'Enter prompt template...',
    description: 'Question to ask the user',
  },
  {
    name: 'timeout',
    type: 'number',
    label: 'Timeout',
    required: true,
    description: 'Response timeout in seconds',
    min: 0,
    max: 3600,
  },
];