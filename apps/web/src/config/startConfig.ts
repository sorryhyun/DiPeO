import { PanelConfig } from '@/types';

export const startConfig: PanelConfig<Record<string, any>> = {
  layout: 'single',
  fields: [
    {
      type: 'text',
      name: 'label',
      label: 'Block Label',
      placeholder: 'Start'
    }
  ]
};