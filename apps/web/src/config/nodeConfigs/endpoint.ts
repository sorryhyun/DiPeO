import type { NodeConfigItem } from '../types';

export const endpointNodeConfig: NodeConfigItem = {
  label: 'Endpoint',
  icon: '🎯',
  color: 'red',
  handles: {
    input: [{ id: 'default', position: 'left' }]
  },
  fields: [
    { 
      name: 'action', 
      type: 'select', 
      label: 'Action', 
      required: true,
      options: [
        { value: 'save', label: 'Save to File' },
        { value: 'output', label: 'Output Result' }
      ]
    },
    { name: 'filename', type: 'string', label: 'Filename', placeholder: 'output.txt' }
  ],
  defaults: { action: 'output', filename: '' }
};