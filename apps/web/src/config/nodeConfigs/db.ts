import type { DBFormData } from '@/types/ui';
import { createUnifiedConfig } from '../unifiedConfig';

/**
 * Unified configuration for Database node
 * This replaces both the node config and panel config
 */
export const dbConfig = createUnifiedConfig<DBFormData>({
  // Node configuration
  label: 'Database',
  icon: '💾',
  color: 'yellow',
  handles: {
    input: [{ id: 'default', position: 'bottom', offset: { x: -20, y: 0 } }],
    output: [{ id: 'default', position: 'bottom', offset: { x: 20, y: 0 } }]
  },
  fields: [
    { 
      name: 'operation', 
      type: 'select', 
      label: 'Operation', 
      required: true,
      options: [
        { value: 'read', label: 'Read File' },
        { value: 'write', label: 'Write File' },
        { value: 'query', label: 'Query Database' }
      ]
    },
    { name: 'path', type: 'string', label: 'Path', required: true, placeholder: 'files/data.json' },
    { 
      name: 'format', 
      type: 'select', 
      label: 'Format', 
      required: true,
      options: [
        { value: 'json', label: 'JSON' },
        { value: 'csv', label: 'CSV' },
        { value: 'text', label: 'Text' }
      ]
    }
  ],
  defaults: { operation: 'read', path: '', format: 'json', label: '', subType: 'fixed_prompt', sourceDetails: '' },
  
  // Panel configuration overrides
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'subType', 'sourceDetails'],
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'Database'
    },
    {
      type: 'select',
      name: 'subType',
      label: 'Source Type',
      options: [
        { value: 'fixed_prompt', label: 'Fixed Prompt' },
        { value: 'file', label: 'File' }
      ]
    },
    {
      type: 'variableTextArea',
      name: 'sourceDetails',
      label: 'Source Details',
      rows: 6,
      placeholder: 'Enter content or file path...',
      validate: (value, formData) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'Source details are required' };
        }
        if (formData?.subType === 'file' && !value.includes('.')) {
          return { isValid: false, error: 'Please provide a valid file path with extension' };
        }
        return { isValid: true };
      }
    }
  ]
});