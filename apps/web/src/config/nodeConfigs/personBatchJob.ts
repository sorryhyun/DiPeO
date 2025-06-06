import type { NodeConfigItem } from '../types';

export const personBatchJobNodeConfig: NodeConfigItem = {
  label: 'Person Batch Job',
  icon: '🤖📦',
  color: 'indigo',
  handles: {
    input: [{ id: 'default', position: 'left' }],
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { name: 'personId', type: 'person', label: 'Person', required: true, placeholder: 'Select person...' },
    { name: 'prompt', type: 'textarea', label: 'Prompt Template', required: true, placeholder: 'Process: {{item}}' },
    { name: 'batchSize', type: 'number', label: 'Batch Size', required: true, min: 1, max: 100 }
  ],
  defaults: { personId: '', prompt: '', batchSize: 10 }
};