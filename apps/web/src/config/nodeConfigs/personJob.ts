import type { NodeConfigItem } from '../types';

export const personJobNodeConfig: NodeConfigItem = {
  label: 'Person Job',
  icon: '🤖',
  color: 'indigo',
  handles: {
    input: [
      { id: 'first', position: 'left', label: 'First', offset: { x: 0, y: -15 } },
      { id: 'default', position: 'left', label: 'Default', offset: { x: 0, y: 15 } }
    ],
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { name: 'personId', type: 'person', label: 'Person', required: true, placeholder: 'Select person...' },
    { name: 'maxIteration', type: 'number', label: 'Max Iterations', required: true, min: 1, max: 100 },
    { name: 'firstOnlyPrompt', type: 'textarea', label: 'First Iteration Prompt', required: true, placeholder: 'Prompt for first iteration (uses "first" input)' },
    { name: 'defaultPrompt', type: 'textarea', label: 'Default Prompt', required: true, placeholder: 'Prompt for subsequent iterations (uses "default" input)' },
    { 
      name: 'contextCleaningRule', 
      type: 'select', 
      label: 'Context Cleaning', 
      required: true,
      options: [
        { value: 'none', label: 'No Cleaning' },
        { value: 'trim', label: 'Trim Old Messages' },
        { value: 'summarize', label: 'Summarize Context' }
      ]
    }
  ],
  defaults: { personId: '', maxIteration: 1, firstOnlyPrompt: '', defaultPrompt: '', contextCleaningRule: 'none' }
};