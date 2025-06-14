import type { EndpointFormData } from '@/types/ui';
import { createUnifiedConfig } from '../unifiedConfig';

/**
 * Unified configuration for Endpoint node
 * This replaces both the node config and panel config
 */
export const endpointConfig = createUnifiedConfig<EndpointFormData>({
  // Node configuration
  label: 'Endpoint',
  icon: '🎯',
  color: 'red',
  handles: {
    input: [{ id: 'default', position: 'left' }]
  },
  fields: [], // Fields are defined in panelCustomFields to match backend expectations
  defaults: { label: '', saveToFile: false, filePath: '', fileFormat: 'text' },
  
  // Panel configuration overrides
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'saveToFile', 'filePath', 'fileFormat'],
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'End'
    },
    {
      type: 'checkbox',
      name: 'saveToFile',
      label: 'Save to File'
    },
    {
      type: 'text',
      name: 'filePath',
      label: 'File Path',
      placeholder: 'files/output.txt',
      conditional: {
        field: 'saveToFile',
        values: [true],
        operator: 'equals'
      },
      validate: (value, formData) => {
        if (formData?.saveToFile && (!value || typeof value !== 'string' || value.trim().length === 0)) {
          return { isValid: false, error: 'File path is required when saving to file' };
        }
        return { isValid: true };
      }
    },
    {
      type: 'select',
      name: 'fileFormat',
      label: 'Format',
      options: [
        { value: 'text', label: 'Text' },
        { value: 'json', label: 'JSON' },
        { value: 'csv', label: 'CSV' }
      ],
      conditional: {
        field: 'saveToFile',
        values: [true],
        operator: 'equals'
      }
    }
  ]
});