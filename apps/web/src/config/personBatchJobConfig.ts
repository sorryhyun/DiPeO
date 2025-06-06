import { PanelConfig } from '@/types';

export const personBatchJobConfig: PanelConfig<Record<string, any>> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'labelPersonRow',
      labelPlaceholder: 'Person Batch Job'
    },
    {
      type: 'row',
      fields: [
        {
          type: 'text',
          name: 'batchSize',
          label: 'Batch Size',
          placeholder: '10',
          className: 'w-24'
        },
        {
          type: 'iterationCount',
          name: 'iterationCount'
        }
      ]
    },
    {
      type: 'checkbox',
      name: 'parallelProcessing',
      label: 'Enable Parallel Processing'
    },
    {
      type: 'row',
      fields: [
        {
          type: 'select',
          name: 'aggregationMethod',
          label: 'Aggregation',
          options: [
            { value: 'concatenate', label: 'Concatenate' },
            { value: 'summarize', label: 'Summarize' },
            { value: 'custom', label: 'Custom' }
          ],
          className: 'flex-1'
        }
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