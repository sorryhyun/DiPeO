import { PanelConfig } from '../../../types';

export const jobConfig: PanelConfig<Record<string, any>> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'row',
      fields: [
        {
          type: 'text',
          name: 'label',
          label: 'Label',
          placeholder: 'Job',
          className: 'flex-1'
        },
        {
          type: 'select',
          name: 'subType',
          label: 'Type',
          options: [
            { value: 'code', label: 'Code Execution' },
            { value: 'api_tool', label: 'API Tool' },
            { value: 'diagram_link', label: 'Diagram Link' }
          ],
          className: 'flex-1'
        }
      ]
    },
    {
      type: 'row',
      fields: [
        {
          type: 'iterationCount',
          name: 'iterationCount',
          label: 'Max Iter',
          className: 'flex-1'
        }
      ]
    }
  ],
  rightColumn: [
    {
      type: 'textarea',
      name: 'sourceDetails',
      label: 'Details',
      rows: 6,
      placeholder: 'Enter job details...',
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