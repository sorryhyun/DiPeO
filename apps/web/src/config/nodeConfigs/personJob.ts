import type { PersonJobFormData } from '@/types/ui';
import { createUnifiedConfig } from '../unifiedConfig';

/**
 * Unified configuration for PersonJob node
 * This replaces both the node config and panel config
 */
export const personJobConfig = createUnifiedConfig<PersonJobFormData>({
  // Node configuration
  label: 'Person Job',
  icon: '🤖',
  color: 'indigo',
  handles: {
    input: [
      { id: 'first', position: 'left', label: 'First', offset: { x: 0, y: -40 }, color: '#f59e0b' },
      { id: 'default', position: 'left', label: 'Default', offset: { x: 0, y: 40 }, color: '#2563eb' }
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
        { value: 'no_forget', label: 'No Forgetting' },
        { value: 'on_every_turn', label: 'Forget on Every Turn' },
        { value: 'upon_request', label: 'Forget Upon Request' }
      ]
    }
  ],
  defaults: { 
    personId: '', 
    maxIteration: 1, 
    firstOnlyPrompt: '', 
    defaultPrompt: '', 
    contextCleaningRule: 'no_forget' 
  },
  
  // Panel configuration overrides
  panelLayout: 'twoColumn',
  panelFieldOrder: ['labelPersonRow', 'contextCleaningRule', 'maxIteration', 'defaultPrompt', 'firstOnlyPrompt'],
  panelFieldOverrides: {
    maxIteration: {
      type: 'maxIteration' // Use the special maxIteration component
    },
    contextCleaningRule: {
      label: 'Forget',
      options: [
        { value: 'upon_request', label: 'Upon This Request' },
        { value: 'no_forget', label: 'Do Not Forget' },
        { value: 'on_every_turn', label: 'On Every Turn' }
      ]
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