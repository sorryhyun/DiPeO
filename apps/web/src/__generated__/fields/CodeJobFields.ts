// Generated field configuration for code_job
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const codeJobFields: UnifiedFieldDefinition[] = [
  {
    name: 'language',
    type: 'text',
    label: '"Language"',
    required: true,
    description: '"Programming language"',
    options: [
      { value: '"SupportedLanguage.PYTHON"', label: '"Python"' },
      { value: '"SupportedLanguage.TYPESCRIPT"', label: '"TypeScript"' },
      { value: '"SupportedLanguage.BASH"', label: '"Bash"' },
      { value: '"SupportedLanguage.SHELL"', label: '"Shell"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'file_path',
    type: 'text',
    label: '"File path"',
    required: false,
    placeholder: '"/path/to/file"',
    description: '"Path to code file"',
  },
  {
    name: 'code',
    type: 'text',
    label: '"Code"',
    required: false,
    description: '"Inline code to execute (alternative to file_path)"',
    rows: 10,
    adjustable: true,
  },
  {
    name: 'function_name',
    type: 'text',
    label: '"Function name"',
    required: false,
    description: '"Function to execute"',
  },
  {
    name: 'timeout',
    type: 'text',
    label: '"Timeout"',
    required: false,
    description: '"Execution timeout in seconds"',
    min: 0,
    max: 3600,
  },
];
