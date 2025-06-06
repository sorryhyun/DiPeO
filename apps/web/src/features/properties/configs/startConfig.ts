import { PanelConfig } from '@/common/types/panelConfig';

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