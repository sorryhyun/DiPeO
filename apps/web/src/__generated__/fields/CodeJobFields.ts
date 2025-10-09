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
];
