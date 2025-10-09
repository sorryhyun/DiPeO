// Generated field configuration for api_job
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const apiJobFields: UnifiedFieldDefinition[] = [
  {
    name: 'url',
    type: 'url',
    label: '"Url"',
    required: true,
    placeholder: '"https://example.com"',
    description: '"API endpoint URL"',
  },
  {
    name: 'method',
    type: 'text',
    label: '"Method"',
    required: true,
    description: '"HTTP method"',
    options: [
      { value: '"HttpMethod.GET"', label: '"GET"' },
      { value: '"HttpMethod.POST"', label: '"POST"' },
      { value: '"HttpMethod.PUT"', label: '"PUT"' },
      { value: '"HttpMethod.DELETE"', label: '"DELETE"' },
      { value: '"HttpMethod.PATCH"', label: '"PATCH"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'headers',
    type: 'textarea',
    label: '"Headers"',
    required: false,
    description: '"HTTP headers"',
  },
  {
    name: 'params',
    type: 'textarea',
    label: '"Params"',
    required: false,
    description: '"Query parameters"',
  },
  {
    name: 'body',
    type: 'textarea',
    label: '"Body"',
    required: false,
    description: '"Request body"',
  },
  {
    name: 'timeout',
    type: 'text',
    label: '"Timeout"',
    required: false,
    description: '"Request timeout in seconds"',
    min: 0,
    max: 3600,
  },
  {
    name: 'auth_type',
    type: 'text',
    label: '"Auth type"',
    required: false,
    description: '"Authentication type"',
    options: [
      { value: '"AuthType.NONE"', label: '"None"' },
      { value: '"AuthType.BEARER"', label: '"Bearer Token"' },
      { value: '"AuthType.BASIC"', label: '"Basic Auth"' },
      { value: '"AuthType.API_KEY"', label: '"API Key"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'auth_config',
    type: 'textarea',
    label: '"Auth config"',
    required: false,
    description: '"Authentication configuration"',
  },
];
