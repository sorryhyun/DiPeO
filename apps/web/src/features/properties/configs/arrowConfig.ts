import { PanelConfig } from '@/common/types/panelConfig';
import { ArrowData } from '@/common/types';

export const arrowConfig: PanelConfig<ArrowData> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'text',
      name: 'label',
      label: 'Arrow Label',
      placeholder: 'e.g., user_query'
    },
    {
      type: 'text',
      name: 'objectKeyPath',
      label: 'Object Key Path',
      placeholder: 'e.g., user.name or data.items[0].value',
      conditional: {
        field: 'contentType',
        values: ['variable_in_object']
      }
    }
  ],
  rightColumn: [
    {
      type: 'select',
      name: 'contentType',
      label: 'Content Type',
      options: [
        { value: 'raw_text', label: 'Raw Text' },
        { value: 'variable_in_object', label: 'Variable in Object' },
        { value: 'conversation_state', label: 'Conversation State' }
      ],
      conditional: {
        field: '_sourceNodeType',
        values: ['start', 'condition'],
        operator: 'notEquals'
      }
    },
    {
      type: 'text',
      name: 'contentTypeDisplay',
      label: 'Content Type',
      placeholder: 'Empty (Fixed)',
      disabled: true,
      conditional: {
        field: '_sourceNodeType',
        values: ['start'],
        operator: 'equals'
      }
    },
    {
      type: 'text',
      name: 'contentTypeDisplay',
      label: 'Content Type',
      placeholder: 'Generic (Fixed)',
      disabled: true,
      conditional: {
        field: '_isFromConditionBranch',
        values: [true],
        operator: 'equals'
      }
    }
  ]
};