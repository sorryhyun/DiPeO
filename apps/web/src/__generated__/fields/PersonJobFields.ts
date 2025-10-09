// Generated field configuration for person_job
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const personJobFields: UnifiedFieldDefinition[] = [
  {
    name: 'tools',
    type: 'text',
    label: '"Tools"',
    required: false,
    description: '"Tools available to the AI agent"',
    column: 1,
    options: [
      { value: '"none"', label: '"None - No tools"' },
      { value: '"image"', label: '"Image - Image generation capabilities"' },
      { value: '"websearch"', label: '"Web Search - Search the internet"' },
    ],
  },
];
