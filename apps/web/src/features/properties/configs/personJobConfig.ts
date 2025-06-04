import { PanelConfig } from '@/common/types/panelConfig';
import { PersonJobBlockData } from '@/common/types';

export const personJobConfig: PanelConfig<PersonJobBlockData> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'labelPersonRow',
      labelPlaceholder: 'Person Job'
    },
    {
      type: 'row',
      fields: [
        {
          type: 'select',
          name: 'contextCleaningRule',
          label: 'Forget',
          options: [
            { value: 'uponRequest', label: 'Upon This Request' },
            { value: 'noForget', label: 'Do Not Forget' },
            { value: 'onEveryTurn', label: 'On Every Turn' }
          ],
          className: 'flex-1'
        },
        {
          type: 'iterationCount',
          name: 'iterationCount',
          className: 'flex-1'
        }
      ]
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