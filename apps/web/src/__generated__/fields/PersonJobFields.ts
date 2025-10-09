// Generated field configuration for person_job
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const personJobFields: UnifiedFieldDefinition[] = [
  {
    name: 'person',
    type: 'text',
    label: '"Person"',
    required: false,
    description: '"AI person to use for this task"',
  },
  {
    name: 'first_only_prompt',
    type: 'text',
    label: '"First only prompt"',
    required: false,
    placeholder: '"Enter prompt template..."',
    description: '"Prompt used only on first execution"',
    rows: 10,
    column: 2,
    adjustable: true,
    showPromptFileButton: true,
  },
  {
    name: 'first_prompt_file',
    type: 'text',
    label: '"First prompt file"',
    required: false,
    placeholder: '"example.txt"',
    description: '"Path to prompt file in /files/prompts/"',
    column: 2,
  },
  {
    name: 'default_prompt',
    type: 'text',
    label: '"Default prompt"',
    required: false,
    placeholder: '"Enter prompt template..."',
    description: '"Prompt template"',
    rows: 10,
    column: 2,
    adjustable: true,
    showPromptFileButton: true,
  },
  {
    name: 'prompt_file',
    type: 'text',
    label: '"Prompt file"',
    required: false,
    placeholder: '"example.txt"',
    description: '"Path to prompt file in /files/prompts/"',
    column: 2,
  },
  {
    name: 'max_iteration',
    type: 'number',
    label: '"Max iteration"',
    required: true,
    description: '"Maximum execution iterations"',
    min: 1,
    validate: (value: unknown) => {
      if (typeof value === 'number' && value < 1) {
        return { isValid: false, error: 'Value must be at least 1' };
      }
      return { isValid: true };
    },
  },
  {
    name: 'memorize_to',
    type: 'text',
    label: '"Memorize to"',
    required: false,
    placeholder: '"e.g., requirements, acceptance criteria, API keys"',
    description: '"Criteria used to select helpful messages for this task. Empty = memorize all. Special: \'GOLDFISH\' for goldfish mode. Comma-separated for multiple criteria."',
    column: 2,
  },
  {
    name: 'at_most',
    type: 'number',
    label: '"At most"',
    required: false,
    description: '"Select at most N messages to keep (system messages may be preserved in addition)."',
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
    name: 'ignore_person',
    type: 'text',
    label: '"Ignore person"',
    required: false,
    placeholder: '"e.g., assistant, user2"',
    description: '"Comma-separated list of person IDs whose messages should be excluded from memory selection."',
    column: 2,
  },
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
  {
    name: 'text_format',
    type: 'text',
    label: '"Text format"',
    required: false,
    placeholder: '"{\"type\": \"object\", \"properties\": {...}}"',
    description: '"JSON schema or response format for structured outputs"',
    rows: 6,
    adjustable: true,
  },
  {
    name: 'text_format_file',
    type: 'text',
    label: '"Text format file"',
    required: false,
    placeholder: '"path/to/models.py"',
    description: '"Path to Python file containing Pydantic models for structured outputs"',
    column: 2,
  },
  {
    name: 'resolved_prompt',
    type: 'text',
    label: '"Resolved prompt"',
    required: false,
    description: '"Pre-resolved prompt content from compile-time"',
    rows: 4,
    adjustable: true,
  },
  {
    name: 'resolved_first_prompt',
    type: 'text',
    label: '"Resolved first prompt"',
    required: false,
    description: '"Pre-resolved first prompt content from compile-time"',
    rows: 4,
    adjustable: true,
  },
  {
    name: 'batch',
    type: 'checkbox',
    label: '"Batch"',
    required: false,
    description: '"Enable batch mode for processing multiple items"',
  },
  {
    name: 'batch_input_key',
    type: 'password',
    label: '"Batch input key"',
    required: false,
    placeholder: '"items"',
    description: '"Key containing the array to iterate over in batch mode"',
  },
  {
    name: 'batch_parallel',
    type: 'checkbox',
    label: '"Batch parallel"',
    required: false,
    description: '"Execute batch items in parallel"',
  },
  {
    name: 'max_concurrent',
    type: 'number',
    label: '"Max concurrent"',
    required: false,
    description: '"Maximum concurrent executions in batch mode"',
    min: 1,
    max: 100,
    validate: (value: unknown) => {
      if (typeof value === 'number' && value < 1) {
        return { isValid: false, error: 'Value must be at least 1' };
      }
      if (typeof value === 'number' && value > 100) {
        return { isValid: false, error: 'Value must be at most 100' };
      }
      return { isValid: true };
    },
  },
];
