import type { JobFormData } from '@/features/diagram-editor/types/panel';
import { createUnifiedConfig } from '../unifiedConfig';

export const jobConfig = createUnifiedConfig<JobFormData>({
  // Node configuration
  label: 'Job',
  icon: '⚙️',
  color: 'blue',
  handles: {
    input: [{ id: 'default', position: 'left' }],
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { 
      name: 'sub_type', 
      type: 'select', 
      label: 'Language', 
      required: true,
      options: [
        { value: 'python', label: 'Python' },
        { value: 'javascript', label: 'JavaScript' },
        { value: 'bash', label: 'Bash' }
      ]
    },
    { name: 'code', type: 'textarea', label: 'Code', required: true, placeholder: 'Enter your code here' }
  ],
  defaults: { sub_type: 'python', code: '', label: '', max_iteration: 1, source_details: '', first_only_prompt: '' },
  
  // Panel configuration overrides
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'sub_type', 'max_iteration', 'source_details', 'first_only_prompt'],
  panelFieldOverrides: {
    sub_type: {
      label: 'Type',
      options: [
        { value: 'code_execution', label: 'Code Execution' },
        { value: 'api_tool', label: 'API Tool' },
        { value: 'diagram_link', label: 'Diagram Link' }
      ]
    }
  },
  panelCustomFields: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'Job'
    },
    {
      type: 'maxIteration',
      name: 'max_iteration',
      label: 'Max Iteration'
    },
    {
      type: 'variableTextArea',
      name: 'sourceDetails',
      label: 'Job Details',
      rows: 6,
      placeholder: 'Enter job details...',
      validate: (value) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'Job details are required' };
        }
        return { isValid: true };
      }
    },
    {
      type: 'variableTextArea',
      name: 'first_only_prompt',
      label: 'First-Only Prompt',
      rows: 4,
      placeholder: 'Prompt to use only on first execution.'
    }
  ]
});