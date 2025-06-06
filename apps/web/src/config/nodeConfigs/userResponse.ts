import type { NodeConfigItem } from '../types';

export const userResponseNodeConfig: NodeConfigItem = {
  label: 'User Response',
  icon: '❓',
  color: 'indigo',
  handles: {
    input: [{ id: 'default', position: 'left' }],
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { name: 'promptMessage', type: 'textarea', label: 'Prompt Message', required: true, placeholder: 'Enter the message to display to the user...' },
    { name: 'timeoutSeconds', type: 'number', label: 'Timeout (seconds)', min: 1, max: 60, placeholder: '10' }
  ],
  defaults: { promptMessage: '', timeoutSeconds: 10 }
};