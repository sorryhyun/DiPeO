import { PanelConfig } from '@/common/types/panelConfig';

export const dbConfig: PanelConfig<Record<string, any>> = {
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
      placeholder: 'For Fixed Prompt: Enter your text content\nFor File: Enter the file path (e.g., data/input.txt)',
    }
  ]
};