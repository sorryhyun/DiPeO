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
    name: 'filePath',
    type: 'text',
    label: '"Filepath"',
    required: false,
    placeholder: '"/path/to/file"',
    description: '"Path to code file"',
  },
  {
    name: 'code',
    type: 'text',
    label: '"Code"',
    required: false,
    description: '"Inline code to execute (alternative to filePath)"',
    rows: 10,
    adjustable: true,
  },
  {
    name: 'functionName',
    type: 'text',
    label: '"Functionname"',
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
