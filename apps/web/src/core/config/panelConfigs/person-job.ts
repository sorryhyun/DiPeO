import type { UnifiedFieldDefinition } from '../field-registry';
import type { PersonJobNodeData } from '@/core/types';

export const personJobFields: UnifiedFieldDefinition<PersonJobNodeData>[] = [
  {
    name: 'labelPersonRow',
    type: 'labelPersonRow',
    label: '',
    required: true,
    labelPlaceholder: 'Enter block label',
    personPlaceholder: 'Select a person'
  },
  {
    name: 'max_iteration',
    type: 'maxIteration',
    label: 'Max Iterations',
    defaultValue: 1,
    min: 1,
    max: 100
  },
  {
    name: 'tools',
    type: 'text',
    label: 'Tools',
    placeholder: 'Optional tools configuration'
  },
  {
    name: 'memory_config.forget_mode',
    type: 'select',
    label: 'Forget Mode',
    options: [
      { value: 'no_forget', label: 'No Forget (Keep all history)' },
      { value: 'on_every_turn', label: 'On Every Turn' },
      { value: 'upon_request', label: 'Upon Request' }
    ],
    defaultValue: 'no_forget'
  },
  {
    name: 'default_prompt',
    type: 'variableTextArea',
    label: 'Default Prompt',
    placeholder: 'Enter default prompt. Use {{variable_name}} for variables.',
    rows: 6,
    showPromptFileButton: true
  },
  {
    name: 'first_only_prompt',
    type: 'variableTextArea',
    label: 'First-Only Prompt',
    required: true,
    placeholder: 'Prompt to use only on first execution.',
    rows: 4,
    showPromptFileButton: true
  }
];