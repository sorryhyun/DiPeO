import { PanelConfig } from '@/shared/types/panelConfig';
import { DBBlockData } from '@/shared/types';

export const dbConfig: PanelConfig<DBBlockData> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'row',
      fields: [
        {
          type: 'text',
          name: 'label',
          label: 'Label',
          placeholder: 'Database',
          className: 'flex-1'
        },
        {
          type: 'select',
          name: 'subType',
          label: 'Source Type',
          options: [
            { value: 'fixed_prompt', label: 'Fixed Prompt' },
            { value: 'file', label: 'File' }
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
      label: 'Source Details',
      rows: 5,
      placeholder: 'Enter source details or file path',
    }
  ]
};