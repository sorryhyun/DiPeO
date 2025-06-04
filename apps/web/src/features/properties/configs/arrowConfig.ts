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
    },
    {
      type: 'checkbox',
      name: 'conversationState',
      label: 'Include Conversation State',
      conditional: {
        field: 'contentType',
        values: ['conversation_state']
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
        field: 'inheritedContentType',
        values: [true],
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
      type: 'select',
      name: 'contentType',
      label: 'Content Type (Inherited)',
      options: [
        { value: 'raw_text', label: 'Raw Text' },
        { value: 'variable_in_object', label: 'Variable in Object' },
        { value: 'conversation_state', label: 'Conversation State' },
        { value: 'generic', label: 'Generic' },
        { value: 'empty', label: 'Empty' }
      ],
      disabled: true,
      conditional: {
        field: 'inheritedContentType',
        values: [true],
        operator: 'equals'
      }
    }
  ]
};