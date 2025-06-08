import type { TypedPanelConfig, PersonBatchJobFormData } from '@/types/ui';

export const personBatchJobPanelConfig: TypedPanelConfig<PersonBatchJobFormData> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'labelPersonRow',
      labelPlaceholder: 'Person Batch Job'
    },
    {
      type: 'text',
      name: 'batchSize',
      label: 'Batch Size',
      placeholder: '10'
    },
    {
      type: 'maxIteration',
      name: 'maxIteration'
    },
    {
      type: 'checkbox',
      name: 'parallelProcessing',
      label: 'Enable Parallel Processing'
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
    }
  ],
  rightColumn: [
    {
      type: 'variableTextArea',
      name: 'batchPrompt',
      label: 'Batch Prompt',
      rows: 6,
      placeholder: 'Enter batch processing prompt. Use {{variable_name}} for variables.'
    },
    {
      type: 'variableTextArea',
      name: 'customAggregationPrompt',
      label: 'Custom Aggregation Prompt',
      rows: 4,
      placeholder: 'Enter custom aggregation prompt to process batch results.',
      conditional: {
        field: 'aggregationMethod',
        values: ['custom']
      }
    }
  ]
};