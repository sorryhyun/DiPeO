// Generated field configuration for api_job
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const apiJobFields: UnifiedFieldDefinition[] = [
  {
    name: 'auth_config',
    type: 'code',
    label: 'Auth Config',
    required: false,
    description: 'Authentication configuration',
  },
  {
    name: 'auth_type',
    type: 'select',
    label: 'Auth Type',
    required: false,
    description: 'Authentication type',
    options: [
      { value: 'none', label: 'None' },
      { value: 'bearer', label: 'Bearer Token' },
      { value: 'basic', label: 'Basic Auth' },
      { value: 'api_key', label: 'API Key' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'body',
    type: 'code',
    label: 'Body',
    required: false,
    description: 'Request body',
  },
  {
    name: 'headers',
    type: 'code',
    label: 'Headers',
    required: false,
    description: 'HTTP headers',
  },
  {
    name: 'method',
    type: 'select',
    label: 'Method',
    required: true,
    description: 'HTTP method',
    options: [
      { value: 'GET', label: 'GET' },
      { value: 'POST', label: 'POST' },
      { value: 'PUT', label: 'PUT' },
      { value: 'DELETE', label: 'DELETE' },
      { value: 'PATCH', label: 'PATCH' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'params',
    type: 'code',
    label: 'Params',
    required: false,
    description: 'Query parameters',
  },
  {
    name: 'timeout',
    type: 'number',
    label: 'Timeout',
    required: false,
    description: 'Request timeout in seconds',
    min: 0,
    max: 3600,
  },
  {
    name: 'url',
    type: 'text',
    label: 'Url',
    required: true,
    placeholder: 'https://example.com',
    description: 'API endpoint URL',
  },
];