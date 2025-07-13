import { HandleLabel } from '@dipeo/domain-models';
import type { PersonBatchJobNodeData } from '@/core/types';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Complete configuration for the Person Batch Job node type
 * Combines visual metadata, node structure, and field definitions
 */
export const PersonBatchJobNodeConfig: UnifiedNodeConfig<PersonBatchJobNodeData> = {
  // Visual metadata
  label: 'Person Batch Job',
  icon: '📦',
  color: '#8b5cf6',
  nodeType: 'person_batch_job' as any, // NodeTypeKey type
  
  // Node structure
  handles: {
    input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
    output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
  },
  
  // Default values
  defaults: { 
    person: '', 
    batch_key: '', 
    prompt: ''
  },
  
  // Panel layout configuration
  panelLayout: 'twoColumn',
  panelFieldOrder: ['labelPersonRow', 'batch_key', 'prompt'],
  
  // Field definitions
  customFields: [
    {
      name: 'labelPersonRow',
      type: 'labelPersonRow',
      label: '',
      required: true,
      labelPlaceholder: 'Enter batch job label',
      personPlaceholder: 'Select a person'
    },
    {
      name: 'batch_key',
      type: 'text',
      label: 'Batch Key',
      required: true,
      placeholder: 'Key containing the array to iterate over',
      column: 1
    },
    {
      name: 'prompt',
      type: 'variableTextArea',
      label: 'Prompt Template',
      required: true,
      placeholder: 'Use {{item}} for current batch item, {{variable_name}} for other variables',
      rows: 5,
      column: 2,
      showPromptFileButton: true,
      validate: (value: unknown) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'Prompt is required' };
        }
        return { isValid: true };
      }
    }
  ]
};