import type { PersonJobFormData } from '@/features/diagram-editor/types/panel';
import { createUnifiedConfig } from '../unifiedConfig';

export const personJobConfig = createUnifiedConfig<PersonJobFormData>({
  // Node configuration
  label: 'Person Job',
  icon: '🤖',
  color: 'indigo',
  handles: {
    input: [
      { id: 'first', position: 'left', label: 'first', offset: { x: 0, y: -60 }, color: '#f59e0b' },
      { id: 'default', position: 'left', label: 'default', offset: { x: 0, y: 60 }, color: '#2563eb' }
    ],
    output: [{ id: 'default', position: 'right' }]
  },
  fields: [
    { name: 'maxIteration', type: 'number', label: 'Max Iterations', required: true, min: 1, max: 100 },
    { name: 'firstOnlyPrompt', type: 'textarea', label: 'First Iteration Prompt', required: true, placeholder: 'Prompt for first iteration (uses "first" input)' },
    { name: 'defaultPrompt', type: 'textarea', label: 'Default Prompt', required: true, placeholder: 'Prompt for subsequent iterations (uses "default" input)' }
  ],
  defaults: { 
    person: '', 
    maxIteration: 1, 
    firstOnlyPrompt: '', 
    defaultPrompt: ''
  },
  
  // Panel configuration overrides
  panelLayout: 'twoColumn',
  panelFieldOrder: ['labelPersonRow', 'maxIteration', 'defaultPrompt', 'firstOnlyPrompt'],
  panelFieldOverrides: {
    maxIteration: {
      type: 'maxIteration' // Use the special maxIteration component
    },
    defaultPrompt: {
      rows: 6,
      placeholder: 'Enter default prompt. Use {{variable_name}} for variables.',
      validate: (value) => {
        if (!value && typeof value !== 'string') {
          return { isValid: false, error: 'Default prompt is recommended' };
        }
        return { isValid: true };
      }
    },
    firstOnlyPrompt: {
      label: 'First-Only Prompt',
      rows: 4,
      placeholder: 'Prompt to use only on first execution.',
      validate: (value) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'First-only prompt is required' };
        }
        return { isValid: true };
      }
    }
  },
  panelCustomFields: [
    {
      type: 'labelPersonRow',
      labelPlaceholder: 'Person Job'
    }
  ]
});