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
    { name: 'max_iteration', type: 'number', label: 'Max Iterations', required: true, min: 1, max: 100 },
    { name: 'first_only_prompt', type: 'textarea', label: 'First Iteration Prompt', required: true, placeholder: 'Prompt for first iteration (uses "first" input)' },
    { name: 'default_prompt', type: 'textarea', label: 'Default Prompt', required: true, placeholder: 'Prompt for subsequent iterations (uses "default" input)' },
    { name: 'tools', type: 'text', label: 'Tools', required: false, placeholder: 'Enter tool names separated by commas (e.g., web_search, image_generation)' }
  ],
  defaults: { 
    person: '', 
    max_iteration: 1, 
    first_only_prompt: '', 
    default_prompt: '',
    tools: ''
  },
  
  // Panel configuration overrides
  panelLayout: 'twoColumn',
  panelFieldOrder: ['labelPersonRow', 'max_iteration', 'tools', 'default_prompt', 'first_only_prompt'],
  panelFieldOverrides: {
    max_iteration: {
      type: 'maxIteration' // Use the special maxIteration component
    },
    default_prompt: {
      rows: 6,
      placeholder: 'Enter default prompt. Use {{variable_name}} for variables.',
      column: 2,
      showPromptFileButton: true,
      validate: (value) => {
        if (!value && typeof value !== 'string') {
          return { isValid: false, error: 'Default prompt is recommended' };
        }
        return { isValid: true };
      }
    },
    first_only_prompt: {
      label: 'First-Only Prompt',
      rows: 4,
      placeholder: 'Prompt to use only on first execution.',
      column: 2,
      showPromptFileButton: true,
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