







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
    label: 'First Only Prompt',
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
    label: 'First Prompt File',
    required: false,
    placeholder: 'example_first.txt',
    description: 'External prompt file for first iteration only',
    column: 2,
  },
  {
    name: 'default_prompt',
    type: 'textarea',
    label: 'Default Prompt',
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
    label: 'Prompt File',
    required: false,
    placeholder: 'example.txt',
    description: 'Path to prompt file in /files/prompts/',
    column: 2,
  },
  {
    name: 'max_iteration',
    type: 'number',
    label: 'Max Iteration',
    required: true,
    defaultValue: 1,
    description: 'Maximum execution iterations',
    min: 1,
  },
  {
    name: 'memory_profile',
    type: 'select',
    label: 'Memory Profile',
    required: false,
    defaultValue: "FOCUSED",
    description: 'Memory profile for conversation context',
    options: [
      { value: 'FULL', label: 'Full 🧠 - No limits, see everything' },
      { value: 'FOCUSED', label: 'Focused 🎯 - Last 20 messages, conversation pairs' },
      { value: 'MINIMAL', label: 'Minimal 💭 - Last 5 messages, system + direct only' },
      { value: 'GOLDFISH', label: 'Goldfish 🐠 - Last 1-2 exchanges only' },
      { value: 'CUSTOM', label: 'Custom ⚙️ - Use memory_settings below' },
    ],
    validate: (value: unknown) => {
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
    label: 'Text Format',
    required: false,
    placeholder: '{\"type\": \"object\", \"properties\": {...}}',
    description: 'JSON schema or response format for structured outputs',
    rows: 6,
    column: 2,
    adjustable: true,
  },
  {
    name: 'memory_settings',
    type: 'group',
    label: 'Memory Settings',
    required: false,
    description: 'Custom memory settings (when memory_profile is CUSTOM)',
    nestedFields: [
      {
        name: 'view',
        type: 'select',
        label: 'View',
        required: true,
        description: 'Memory view type',
        uiConfig: {
          inputType: 'select',
          options: [
            { value: 'FULL_CONVERSATION', label: 'Full Conversation' },
            { value: 'RELATED_CONVERSATION_PAIRS', label: 'Related Conversation Pairs' },
            { value: 'DIRECT_MESSAGES', label: 'Direct Messages' },
            { value: 'SYSTEM_AND_DIRECT', label: 'System and Direct' },
          ],
        },
      },
      {
        name: 'max_messages',
        type: 'number',
        label: 'Max Messages',
        required: false,
        description: 'Maximum number of messages to retain',
        uiConfig: {
          inputType: 'number',
          min: 1,
          max: 100,
        },
      },
      {
        name: 'preserve_system',
        type: 'checkbox',
        label: 'Preserve System',
        required: false,
        description: 'Always preserve system messages',
        defaultValue: true,
        uiConfig: {
          inputType: 'checkbox',
        },
      },
    ],
  },
];