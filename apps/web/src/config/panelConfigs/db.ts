import type { PanelConfig } from '@/types';

export const dbPanelConfig: PanelConfig<Record<string, any>> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'text',
      name: 'label',
      label: 'Label',
      placeholder: 'Database'
    },
    {
      type: 'select',
      name: 'subType',
      label: 'Source Type',
      options: [
        { value: 'fixed_prompt', label: 'Fixed Prompt' },
        { value: 'file', label: 'File' }
      ]
    }
  ],
  rightColumn: [
    {
      type: 'textarea',
      name: 'sourceDetails',
      label: 'Source Details',
      rows: 5,
      placeholder: 'For Fixed Prompt: Enter your text content\nFor File: Enter the file path (e.g., data/input.txt)'
    }
  ]
};