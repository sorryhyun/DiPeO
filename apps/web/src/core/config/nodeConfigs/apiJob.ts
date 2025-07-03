import type { ApiJobFormData } from '@/features/diagram-editor/types/panel';
import { createUnifiedConfig } from '../unifiedConfig';

export const apiJobConfig = createUnifiedConfig<ApiJobFormData>({
  // Node configuration
  label: 'API Job',
  icon: '🌐',
  color: 'green',
  handles: {
    input: [{ id: 'default', position: 'left' }],
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { 
      name: 'url', 
      type: 'string', 
      label: 'URL', 
      required: true,
      placeholder: 'https://api.example.com/endpoint'
    },
    { 
      name: 'method', 
      type: 'select', 
      label: 'HTTP Method', 
      required: true,
      options: [
        { value: 'GET', label: 'GET' },
        { value: 'POST', label: 'POST' },
        { value: 'PUT', label: 'PUT' },
        { value: 'DELETE', label: 'DELETE' },
        { value: 'PATCH', label: 'PATCH' }
      ]
    },
    {
      name: 'headers',
      type: 'textarea',
      label: 'Headers (JSON)',
      required: false,
      placeholder: '{"Content-Type": "application/json"}',
      rows: 3
    },
    {
      name: 'params',
      type: 'textarea',
      label: 'Query Parameters (JSON)',
      required: false,
      placeholder: '{"key": "value"}',
      rows: 3
    },
    {
      name: 'body',
      type: 'textarea',
      label: 'Request Body (JSON)',
      required: false,
      placeholder: '{"data": "value"}',
      rows: 4
    },
    {
      name: 'auth_type',
      type: 'select',
      label: 'Authentication',
      required: false,
      options: [
        { value: 'none', label: 'None' },
        { value: 'bearer', label: 'Bearer Token' },
        { value: 'basic', label: 'Basic Auth' },
        { value: 'api_key', label: 'API Key' }
      ]
    },
    {
      name: 'auth_config',
      type: 'textarea',
      label: 'Auth Config (JSON)',
      required: false,
      placeholder: '{"token": "your-token"}',
      rows: 2
    },
    { 
      name: 'timeout', 
      type: 'number', 
      label: 'Timeout (seconds)', 
      required: false,
      min: 1,
      max: 300,
      placeholder: '30'
    }
  ],
  defaults: { 
    url: '',
    method: 'GET',
    headers: {},
    params: {},
    body: null,
    auth_type: 'none',
    auth_config: {},
    timeout: 30,
    label: 'API Call'
  },
  
  // Panel configuration
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'method', 'auth_type', 'timeout', 'url', 'headers', 'params', 'body', 'auth_config'],
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Label',
      placeholder: 'API Call',
      column: 1
    }
  ],
  panelFieldOverrides: {
    method: { column: 1 },
    auth_type: { column: 1 },
    timeout: { column: 1 },
    url: { column: 2 },
    headers: { column: 2 },
    params: { column: 2 },
    body: { column: 2 },
    auth_config: { column: 2 }
  }
});