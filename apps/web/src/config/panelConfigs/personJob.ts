import type { TypedPanelConfig, PersonJobFormData } from '@/types/ui';

export const personJobPanelConfig: TypedPanelConfig<PersonJobFormData> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'labelPersonRow',
      labelPlaceholder: 'Person Job'
    },
    {
      type: 'select',
      name: 'contextCleaningRule',
      label: 'Forget',
      options: [
        { value: 'upon_request', label: 'Upon This Request' },
        { value: 'no_forget', label: 'Do Not Forget' },
        { value: 'on_every_turn', label: 'On Every Turn' }
      ]
    },
    {
      type: 'maxIteration',
      name: 'maxIteration'
    }
  ],
  rightColumn: [
    {
      type: 'variableTextArea',
      name: 'defaultPrompt',
      label: 'Default Prompt',
      rows: 6,
      placeholder: 'Enter default prompt. Use {{variable_name}} for variables.',
      validate: (value) => {
        if (!value && typeof value !== 'string') {
          return { isValid: false, error: 'Default prompt is recommended' };
        }
        return { isValid: true };
      }
    },
    {
      type: 'variableTextArea',
      name: 'firstOnlyPrompt',
      label: 'First-Only Prompt',
      rows: 4,
      placeholder: 'Prompt to use only on first execution.',
      required: true,
      validate: (value) => {
        if (!value || typeof value !== 'string' || value.trim().length === 0) {
          return { isValid: false, error: 'First-only prompt is required' };
        }
        return { isValid: true };
      }
    }
  ]
};