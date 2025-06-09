import type { NodeConfigItem } from '@/types/config';

export const startNodeConfig: NodeConfigItem = {
  label: 'Start',
  icon: '🚀',
  color: 'green',
  handles: {
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { name: 'output', type: 'textarea', label: 'Output Data', required: true, placeholder: 'Enter static data to output' }
  ],
  defaults: { output: '' }
};