import { createUnifiedConfig } from '../unifiedConfig';

// Define type inline to satisfy constraint
type DBFormDataType = {
  label?: string;
  sub_type?: string;
  sourceDetails?: string;
  operation?: string;
  [key: string]: unknown;
};

/**
 * Unified configuration for Database node
 * This replaces both the node config and panel config
 */
export const dbConfig = createUnifiedConfig<DBFormDataType>({
  // Node configuration
  label: 'Database',
  icon: '💾',
  color: 'yellow',
  handles: {
    input: [{ id: 'default', position: 'bottom', offset: { x: -30, y: 0 } }],
    output: [{ id: 'default', position: 'bottom', offset: { x: 30, y: 0 } }]
  },
  fields: [], // Fields are defined in panelCustomFields to match backend expectations
  defaults: { label: '', sub_type: 'fixed_prompt', sourceDetails: '', operation: 'read' },
  
  // Panel configuration overrides
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'sub_type', 'operation', 'sourceDetails'],
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'Database',
      column: 1
    },
    {
      type: 'select',
      name: 'sub_type',
      label: 'Source Type',
      options: [
        { value: 'fixed_prompt', label: 'Fixed Prompt' },
        { value: 'file', label: 'File' }
      ],
      column: 1
    },
    {
      type: 'select',
      name: 'operation',
      label: 'Operation',
      options: [
        { value: 'read', label: 'Read' },
        { value: 'write', label: 'Write' },
        { value: 'update', label: 'Update' },
        { value: 'delete', label: 'Delete' }
      ],
      column: 1
    },
    {
      type: 'variableTextArea',
      name: 'sourceDetails',
      label: 'Source Details',
      rows: 6,
      placeholder: 'Enter content or file path...',
      column: 2,
      validate: (value, formData) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'Source details are required' };
        }
        if (formData?.sub_type === 'file' && !value.includes('.')) {
          return { isValid: false, error: 'Please provide a valid file path with extension' };
        }
        return { isValid: true };
      }
    }
  ]
});