// Generated field configuration for api_job
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const apiJobFields: UnifiedFieldDefinition[] = [
  {
    name: 'url',
    type: 'text',
    label: 'Url',
    required: true,
    placeholder: 'https://example.com',
    description: 'API endpoint URL',
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
    name: 'headers',
    type: 'code',
    label: 'Headers',
    required: false,
    description: 'HTTP headers',
  },
  {
    name: 'params',
    type: 'code',
    label: 'Params',
    required: false,
    description: 'Query parameters',
  },
  {
    name: 'body',
    type: 'code',
    label: 'Body',
    required: false,
    description: 'Request body',
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
    name: 'auth_type',
    type: 'select',
    label: 'Auth type',
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
    name: 'auth_config',
    type: 'code',
    label: 'Auth config',
    required: false,
    description: 'Authentication configuration',
  },
];
