import type { PanelConfig } from '@/types';

export const personJobPanelConfig: PanelConfig<Record<string, any>> = {
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
    },
    {
      type: 'checkbox',
      name: 'interactive',
      label: 'Interactive Mode - Wait for user input before LLM call'
    }
  ],
  rightColumn: [
    {
      type: 'variableTextArea',
      name: 'defaultPrompt',
      label: 'Default Prompt',
      rows: 6,
      placeholder: 'Enter default prompt. Use {{variable_name}} for variables.'
    },
    {
      type: 'variableTextArea',
      name: 'firstOnlyPrompt',
      label: 'First-Only Prompt',
      rows: 4,
      placeholder: 'Prompt to use only on first execution.'
    }
  ]
};