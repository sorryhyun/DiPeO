import { PanelConfig } from '@/common/types/panelConfig';
import { StartBlockData } from '@/common/types';

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