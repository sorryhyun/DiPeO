import type { PanelConfig } from '@/types';

export const startPanelConfig: PanelConfig<Record<string, any>> = {
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