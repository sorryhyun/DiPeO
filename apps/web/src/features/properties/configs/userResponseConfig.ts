import { PanelConfig } from '@/common/types/panelConfig';
import { UserResponseBlockData } from '@/common/types/node';

export const userResponseConfig: PanelConfig<UserResponseBlockData> = {
  layout: 'single',
  fields: [
    {
      type: 'text',
      name: 'label',
      label: 'Name',
      placeholder: 'User Response',
    },
    {
      type: 'textarea',
      name: 'prompt',
      label: 'Prompt Message',
      placeholder: 'Enter the message to show to the user...',
      rows: 3,
    },
    {
      type: 'text',
      name: 'timeout',
      label: 'Timeout (seconds)',
      placeholder: '10',
    },
  ],
};