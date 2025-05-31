import { PanelConfig } from '@/shared/types/panelConfig';
import { StartBlockData } from '@/shared/types';

export const startConfig: PanelConfig<StartBlockData> = {
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