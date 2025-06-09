import type { JobFormData } from '@/types/ui';
import { createUnifiedConfig } from '../unifiedConfig';

/**
 * Unified configuration for Job node
 * This replaces both the node config and panel config
 */
export const jobUnifiedConfig = createUnifiedConfig<JobFormData>({
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
      name: 'subType', 
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
  defaults: { subType: 'python', code: '', label: '', maxIteration: 1, sourceDetails: '', firstOnlyPrompt: '' },
  
  // Panel configuration overrides
  panelLayout: 'twoColumn',
  panelFieldOrder: ['label', 'subType', 'maxIteration', 'sourceDetails', 'firstOnlyPrompt'],
  panelFieldOverrides: {
    subType: {
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
      name: 'maxIteration',
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
      name: 'firstOnlyPrompt',
      label: 'First-Only Prompt',
      rows: 4,
      placeholder: 'Prompt to use only on first execution.'
    }
  ]
});