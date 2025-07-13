import { HandleLabel, NodeType } from '@dipeo/domain-models';
import type { ApiJobNodeData } from '@/core/types';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the API Job node type
 * Combines visual metadata, node structure, and field definitions
 */
export const ApiJobNodeConfig: UnifiedNodeConfig<ApiJobNodeData> = {
  // Visual metadata
  label: 'API Job',
  icon: '🌐',
  color: '#06b6d4',
  nodeType: 'api_job' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
    output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
  },
  
  // Default values
  defaults: { 
    label: 'API Job', 
    url: '', 
    method: 'GET', 
    headers: '', 
    body: '' 
  },
  
  // Panel layout configuration
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'url', 'method', 'headers', 'body'],
  
  // Field definitions
  customFields: [
    {
      name: 'label',
      type: 'text',
      label: 'Label',
      required: true,
      placeholder: 'Enter API job label'
    },
    {
      name: 'url',
      type: 'text',
      label: 'URL',
      required: true,
      placeholder: 'https://api.example.com/endpoint',
      column: 1
    },
    {
      name: 'method',
      type: 'select',
      label: 'Method',
      required: true,
      options: [
        { value: 'GET', label: 'GET' },
        { value: 'POST', label: 'POST' },
        { value: 'PUT', label: 'PUT' },
        { value: 'DELETE', label: 'DELETE' },
        { value: 'PATCH', label: 'PATCH' }
      ],
      defaultValue: 'GET',
      column: 1
    },
    {
      name: 'headers',
      type: 'variableTextArea',
      label: 'Headers (JSON)',
      placeholder: '{"Content-Type": "application/json"}',
      rows: 4,
      column: 2
    },
    {
      name: 'body',
      type: 'variableTextArea',
      label: 'Body',
      placeholder: 'Request body (for POST, PUT, PATCH)',
      rows: 6,
      column: 2,
      conditional: {
        field: 'method',
        values: ['POST', 'PUT', 'PATCH'],
        operator: 'includes'
      }
    }
  ]
};