import type { TypedPanelConfig, JobFormData } from '@/types/ui';

export const jobPanelConfig: TypedPanelConfig<JobFormData> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'text',
      name: 'label',
      label: 'Label',
      placeholder: 'Job'
    },
    {
      type: 'select',
      name: 'subType',
      label: 'Type',
      options: [
        { value: 'code', label: 'Code Execution' },
        { value: 'api_tool', label: 'API Tool' },
        { value: 'diagram_link', label: 'Diagram Link' }
      ]
    },
    {
      type: 'maxIteration',
      name: 'maxIteration',
      label: 'Max Iter'
    }
  ],
  rightColumn: [
    {
      type: 'textarea',
      name: 'sourceDetails',
      label: 'Details',
      rows: 6,
      placeholder: 'Enter job details...'
    },
    {
      type: 'textarea',
      name: 'firstOnlyPrompt',
      label: 'First-Only Prompt',
      rows: 4,
      placeholder: 'Prompt to use only on first execution.'
    }
  ]
};