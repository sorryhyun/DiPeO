// Generated field configuration for hook
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const hookFields: UnifiedFieldDefinition[] = [
  {
    name: 'hook_type',
    type: 'select',
    label: 'Hook Type',
    required: true,
    defaultValue: 'shell',
    description: 'Type of hook to execute',
    options: [
      { value: 'shell', label: 'Shell' },
      { value: 'http', label: 'Http' },
      { value: 'python', label: 'Python' },
      { value: 'file', label: 'File' },
    ],
  },
  {
    name: 'command',
    type: 'text',
    label: 'Command',
    required: false,
    placeholder: 'Command to execute',
    description: 'Shell command to run (for shell hooks)',
  },
  {
    name: 'url',
    type: 'text',
    label: 'Url',
    required: false,
    placeholder: 'https://api.example.com/webhook',
    description: 'Webhook URL (for HTTP hooks)',
  },
  {
    name: 'timeout',
    type: 'number',
    label: 'Timeout',
    required: false,
    defaultValue: 60,
    description: 'Execution timeout in seconds',
  },
  {
    name: 'retry_count',
    type: 'number',
    label: 'Retry Count',
    required: false,
    description: 'Number of retries on failure',
  },
];