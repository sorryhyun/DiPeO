import { HandleLabel, NodeType } from '@dipeo/domain-models';
import type { CodeJobNodeData } from '@/core/types';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the Code Job node type
 * Combines visual metadata, node structure, and field definitions
 */
export const CodeJobNodeConfig: UnifiedNodeConfig<CodeJobNodeData> = {
  // Visual metadata
  label: 'Code Job',
  icon: '💻',
  color: '#4ade80',
  nodeType: 'code_job' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
    output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
  },
  
  // Default values
  defaults: { 
    label: 'Code Job', 
    language: 'python', 
    code: '' 
  },
  
  // Panel layout configuration
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'language', 'code'],
  
  // Field definitions
  customFields: [
    {
      name: 'label',
      type: 'text',
      label: 'Label',
      required: true,
      placeholder: 'Enter code job label'
    },
    {
      name: 'language',
      type: 'select',
      label: 'Language',
      required: true,
      options: [
        { value: 'python', label: 'Python' },
        { value: 'javascript', label: 'JavaScript' },
        { value: 'typescript', label: 'TypeScript' }
      ],
      column: 1
    },
    {
      name: 'code',
      type: 'variableTextArea',
      label: 'Code',
      required: true,
      placeholder: 'Enter your code here',
      rows: 8,
      column: 2,
      validate: (value: unknown) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'Code is required' };
        }
        return { isValid: true };
      }
    }
  ]
};