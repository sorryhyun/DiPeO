import { PanelConfig } from '@/shared/types/panelConfig';
import { JobBlockData } from '@/shared/types';

export const jobConfig: PanelConfig<JobBlockData> = {
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
    }
  ],
  rightColumn: [
    {
      type: 'textarea',
      name: 'sourceDetails',
      label: 'Details',
      rows: 8,
      placeholder: 'Enter job details...',
    }
  ]
};