// Generated field configuration for person_job
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const personJobFields: UnifiedFieldDefinition[] = [
  {
    name: 'person',
    type: 'personSelect',
    label: 'Person',
    required: false,
    description: 'AI person to use',
  },
  {
    name: 'first_only_prompt',
    type: 'textarea',
    label: 'First only prompt',
    required: true,
    placeholder: 'Enter prompt template...',
    description: 'Prompt used only on first execution',
    rows: 10,
    column: 2,
    adjustable: true,
    showPromptFileButton: true,
  },
  {
    name: 'first_prompt_file',
    type: 'text',
    label: 'First prompt file',
    required: false,
    placeholder: 'example_first.txt',
    description: 'External prompt file for first iteration only',
    column: 2,
  },
  {
    name: 'default_prompt',
    type: 'textarea',
    label: 'Default prompt',
    required: false,
    placeholder: 'Enter prompt template...',
    description: 'Default prompt template',
    rows: 10,
    column: 2,
    adjustable: true,
    showPromptFileButton: true,
  },
  {
    name: 'prompt_file',
    type: 'text',
    label: 'Prompt file',
    required: false,
    placeholder: 'example.txt',
    description: 'Path to prompt file in /files/prompts/',
    column: 2,
  },
  {
    name: 'max_iteration',
    type: 'number',
    label: 'Max iteration',
    required: true,
    defaultValue: 100,
    description: 'Maximum execution iterations',
    min: 1,
  },
  {
    name: 'memorize_to',
    type: 'text',
    label: 'Memorize to',
    required: false,
    placeholder: 'e.g., requirements, acceptance criteria, API keys',
    description: 'Criteria used to select helpful messages for this task. Empty = memorize all. Special: \'GOLDFISH\' for goldfish mode. Comma-separated for multiple criteria.',
    column: 2,
  },
  {
    name: 'at_most',
    type: 'number',
    label: 'At most',
    required: false,
    description: 'Select at most N messages to keep (system messages may be preserved in addition).',
    column: 1,
    min: 1,
    max: 500,
    validate: (value: unknown) => {
      if (typeof value === 'number' && value < 1) {
        return { isValid: false, error: 'Value must be at least 1' };
      }
      if (typeof value === 'number' && value > 500) {
        return { isValid: false, error: 'Value must be at most 500' };
      }
      return { isValid: true };
    },
  },
  {
    name: 'tools',
    type: 'select',
    label: 'Tools',
    required: false,
    defaultValue: "none",
    description: 'Tools available to the AI agent',
    column: 1,
    options: [
      { value: 'none', label: 'None - No tools' },
      { value: 'image', label: 'Image - Image generation capabilities' },
      { value: 'websearch', label: 'Web Search - Search the internet' },
    ],
  },
  {
    name: 'text_format',
    type: 'textarea',
    label: 'Text format',
    required: false,
    placeholder: '{\"type\": \"object\", \"properties\": {...}}',
    description: 'JSON schema or response format for structured outputs',
    rows: 6,
    column: 2,
    adjustable: true,
  },
];