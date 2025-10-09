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
      { value: '"python"', label: '"Python"' },
      { value: '"typescript"', label: '"TypeScript"' },
      { value: '"bash"', label: '"Bash"' },
      { value: '"shell"', label: '"Shell"' },
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
    description: '"Operation timeout in seconds"',
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
