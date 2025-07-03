import type { PersonBatchJobFormData } from '@/features/diagram-editor/types/panel';
import { createUnifiedConfig } from '../unifiedConfig';

export const personBatchJobConfig = createUnifiedConfig<PersonBatchJobFormData>({
  // Node configuration
  label: 'Person Batch Job',
  icon: '🤖📦',
  color: 'indigo',
  handles: {
    input: [{ id: 'default', position: 'left' }],
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { name: 'person', type: 'person', label: 'Person', required: true, placeholder: 'Select person...' },
    { name: 'prompt', type: 'textarea', label: 'Prompt', required: true, placeholder: 'Enter prompt template' },
    { name: 'batchSize', type: 'number', label: 'Batch Size', required: true, min: 1, max: 100 }
  ],
  defaults: { 
    person: '', 
    prompt: '', 
    batchSize: 10,
    max_iteration: 1,
    parallel_processing: false,
    aggregation_method: 'concatenate',
    batchPrompt: '',
    customAggregationPrompt: ''
  },
  
  // Panel configuration overrides
  panelLayout: 'twoColumn',
  panelFieldOrder: ['labelPersonRow', 'batchSize', 'max_iteration', 'parallelProcessing', 'aggregationMethod', 'batchPrompt', 'customAggregationPrompt'],
  panelFieldOverrides: {
    batchSize: {
      type: 'text',
      validate: (value) => {
        const num = parseInt(value as string, 10);
        if (isNaN(num) || num < 1 || num > 100) {
          return { isValid: false, error: 'Batch size must be between 1 and 100' };
        }
        return { isValid: true };
      }
    }
  },
  panelCustomFields: [
    {
      type: 'labelPersonRow',
      labelPlaceholder: 'Batch Process'
    },
    {
      type: 'maxIteration',
      name: 'max_iteration',
      label: 'Max Iteration'
    },
    {
      type: 'checkbox',
      name: 'parallelProcessing',
      label: 'Parallel Processing'
    },
    {
      type: 'select',
      name: 'aggregationMethod',
      label: 'Aggregation',
      options: [
        { value: 'concatenate', label: 'Concatenate' },
        { value: 'summarize', label: 'Summarize' },
        { value: 'custom', label: 'Custom' }
      ]
    },
    {
      type: 'variableTextArea',
      name: 'batchPrompt',
      label: 'Batch Prompt',
      rows: 6,
      placeholder: 'Process each item: {{item}}',
      showPromptFileButton: true,
      validate: (value) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'Batch prompt is required' };
        }
        return { isValid: true };
      }
    },
    {
      type: 'variableTextArea',
      name: 'customAggregationPrompt',
      label: 'Custom Aggregation',
      rows: 4,
      placeholder: 'Aggregate results: {{results}}',
      showPromptFileButton: true,
      conditional: {
        field: 'aggregationMethod',
        values: ['custom'],
        operator: 'equals'
      }
    }
  ]
});