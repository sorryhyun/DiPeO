import { HandleLabel, NodeType } from '@dipeo/domain-models';
import type { DBNodeData } from '@/core/types';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the Database node type
 * Combines visual metadata, node structure, and field definitions
 */
export const DbNodeConfig: UnifiedNodeConfig<DBNodeData> = {
  // Visual metadata
  label: 'Database',
  icon: '💾',
  color: '#6366f1',
  nodeType: 'db' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'bottom', offset: { x: -30, y: 0 } }],
    output: [{ id: HandleLabel.DEFAULT, position: 'bottom', offset: { x: 30, y: 0 } }]
  },
  
  // Default values
  defaults: { 
    label: 'Database', 
    sub_type: 'fixed_prompt', 
    source_details: '', 
    operation: 'read' 
  },
  
  // Panel layout configuration
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'sub_type', 'operation', 'source_details'],
  
  // Field definitions
  customFields: [
    {
      name: 'label',
      type: 'text',
      label: 'Label',
      required: true,
      placeholder: 'Enter database label',
      column: 1
    },
    {
      name: 'sub_type',
      type: 'select',
      label: 'Source Type',
      required: true,
      options: [
        { value: 'fixed_prompt', label: 'Fixed Prompt' },
        { value: 'file', label: 'File' }
      ],
      column: 1
    },
    {
      name: 'operation',
      type: 'select',
      label: 'Operation',
      required: true,
      options: [
        { value: 'prompt', label: 'Prompt' },
        { value: 'read', label: 'Read' },
        { value: 'write', label: 'Write' },
        { value: 'update', label: 'Update' },
        { value: 'delete', label: 'Delete' }
      ],
      column: 1
    },
    {
      name: 'source_details',
      type: 'variableTextArea',
      label: 'Source Details',
      placeholder: 'Enter content or file path...',
      rows: 6,
      column: 2,
      showPromptFileButton: true,
      validate: (value: unknown, formData: DBNodeData) => {
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
};