import { HandleLabel, NodeType } from '@dipeo/domain-models';
import type { EndpointNodeData } from '@/core/types';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the Endpoint node type
 * Combines visual metadata, node structure, and field definitions
 */
export const EndpointNodeConfig: UnifiedNodeConfig<EndpointNodeData> = {
  // Visual metadata
  label: 'Endpoint',
  icon: '🎯',
  color: '#ef4444',
  nodeType: 'endpoint' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'right' }]
  },
  
  // Default values
  defaults: { 
    label: 'Endpoint', 
    output_variable: '', 
    save_to_file: false, 
    file_format: 'json', 
    file_name: '' 
  },
  
  // Panel layout configuration
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'output_variable', 'save_to_file', 'file_format', 'file_name'],
  
  // Field definitions
  customFields: [
    {
      name: 'label',
      type: 'text',
      label: 'Label',
      required: true,
      placeholder: 'Enter endpoint label',
      column: 1
    },
    {
      name: 'output_variable',
      type: 'text',
      label: 'Output Variable',
      placeholder: 'Variable to store the output',
      column: 1
    },
    {
      name: 'save_to_file',
      type: 'checkbox',
      label: 'Save to File',
      defaultValue: false,
      column: 2
    },
    {
      name: 'file_format',
      type: 'select',
      label: 'File Format',
      options: [
        { value: 'json', label: 'JSON' },
        { value: 'yaml', label: 'YAML' },
        { value: 'csv', label: 'CSV' },
        { value: 'txt', label: 'Text' }
      ],
      defaultValue: 'json',
      column: 2,
      conditional: {
        field: 'save_to_file',
        values: [true]
      }
    },
    {
      name: 'file_name',
      type: 'text',
      label: 'File Name',
      placeholder: 'output.json',
      column: 2,
      conditional: {
        field: 'save_to_file',
        values: [true]
      },
      validate: (value: unknown, formData: EndpointNodeData) => {
        if (formData?.save_to_file && (!value || typeof value !== 'string' || value.trim().length === 0)) {
          return { isValid: false, error: 'File name is required when saving to file' };
        }
        return { isValid: true };
      }
    }
  ]
};