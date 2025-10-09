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
      { value: '"GET"', label: '"GET"' },
      { value: '"POST"', label: '"POST"' },
      { value: '"PUT"', label: '"PUT"' },
      { value: '"DELETE"', label: '"DELETE"' },
      { value: '"PATCH"', label: '"PATCH"' },
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
    name: 'auth_type',
    type: 'text',
    label: '"Auth type"',
    required: false,
    description: '"Authentication type"',
    options: [
      { value: '"none"', label: '"None"' },
      { value: '"bearer"', label: '"Bearer Token"' },
      { value: '"basic"', label: '"Basic Auth"' },
      { value: '"api_key"', label: '"API Key"' },
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
