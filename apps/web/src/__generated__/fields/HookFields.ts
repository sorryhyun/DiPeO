// Generated field configuration for hook
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const hookFields: UnifiedFieldDefinition[] = [
  {
    name: 'hook_type',
    type: 'text',
    label: '"Hook type"',
    required: true,
    description: '"Type of hook to execute"',
    options: [
      { value: '"HookType.SHELL"', label: '"Shell"' },
      { value: '"HookType.HTTP"', label: '"HTTP"' },
      { value: '"HookType.PYTHON"', label: '"Python"' },
      { value: '"HookType.FILE"', label: '"File"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'command',
    type: 'text',
    label: '"Command"',
    required: false,
    placeholder: '"Command to execute"',
    description: '"Shell command to run (for shell hooks)"',
  },
  {
    name: 'url',
    type: 'url',
    label: '"Url"',
    required: false,
    placeholder: '"https://api.example.com/webhook"',
    description: '"Webhook URL (for HTTP hooks)"',
    validate: (value: unknown) => {
      if (typeof value === 'string' && !new RegExp('^https?://.+').test(value)) {
        return { isValid: false, error: 'Invalid format' };
      }
      return { isValid: true };
    },
  },
  {
    name: 'timeout',
    type: 'text',
    label: '"Timeout"',
    required: false,
    description: '"Execution timeout in seconds"',
    min: 1,
    max: 300,
    validate: (value: unknown) => {
      if (typeof value === 'number' && value < 1) {
        return { isValid: false, error: 'Value must be at least 1' };
      }
      if (typeof value === 'number' && value > 300) {
        return { isValid: false, error: 'Value must be at most 300' };
      }
      return { isValid: true };
    },
  },
  {
    name: 'retry_count',
    type: 'number',
    label: '"Retry count"',
    required: false,
    description: '"Number of retries on failure"',
    min: 0,
    max: 5,
    validate: (value: unknown) => {
      if (typeof value === 'number' && value < 0) {
        return { isValid: false, error: 'Value must be at least 0' };
      }
      if (typeof value === 'number' && value > 5) {
        return { isValid: false, error: 'Value must be at most 5' };
      }
      return { isValid: true };
    },
  },
];
