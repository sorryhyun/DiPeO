import { PanelConfig } from '@/shared/types/panelConfig';
import { EndpointBlockData } from '@/shared/types';

export const endpointConfig: PanelConfig<EndpointBlockData> = {
  layout: 'single',
  fields: [
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
      type: 'text',
      name: 'filePath',
      label: 'File Path',
      placeholder: 'results/output.txt',
      conditional: {
        field: 'saveToFile',
        values: [true]
      }
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
      }
    }
  ]
};