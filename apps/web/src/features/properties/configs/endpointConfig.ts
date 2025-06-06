import { PanelConfig } from '../../../types';

export const endpointConfig: PanelConfig<Record<string, any>> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'End'
    },
    {
      type: 'checkbox',
      name: 'saveToFile',
      label: 'Save output to file'
    },
    {
      type: 'row',
      fields: [
        {
          type: 'text',
          name: 'filePath',
          label: 'File Path',
          placeholder: 'results/output.txt',
          conditional: {
            field: 'saveToFile',
            values: [true]
          },
          className: 'flex-1'
        },
        {
          type: 'select',
          name: 'fileFormat',
          label: 'File Format',
          options: [
            { value: 'text', label: 'Plain Text' },
            { value: 'json', label: 'JSON' },
            { value: 'csv', label: 'CSV' }
          ],
          conditional: {
            field: 'saveToFile',
            values: [true]
          },
          className: 'flex-1'
        }
      ]
    }
  ],
  rightColumn: []
};