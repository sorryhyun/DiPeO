import { PanelConfig } from '@/common/types/panelConfig';
import { ArrowData } from '@/common/types';

export const arrowConfig: PanelConfig<ArrowData> = {
  layout: 'twoColumn',
  leftColumn: [
    {
      type: 'text',
      name: 'label',
      label: 'Arrow Label',
      placeholder: 'e.g., user_query',
      conditional: {
        field: '_sourceNodeType',
        values: ['condition'],
        operator: 'notEquals'
      }
    },
    {
      type: 'text',
      name: 'label',
      label: 'Arrow Label (Inherited from input)',
      placeholder: 'Inherited from condition input',
      disabled: true,
      conditional: {
        field: '_sourceNodeType',
        values: ['condition'],
        operator: 'equals'
      }
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
        values: ['condition', 'start'],
        operator: 'notEquals'
      }
    },
    {
      type: 'select',
      name: 'contentType',
      label: 'Content Type (Inherited from condition input)',
      options: [
        { value: 'raw_text', label: 'Raw Text' },
        { value: 'variable_in_object', label: 'Variable in Object' },
        { value: 'conversation_state', label: 'Conversation State' },
        { value: 'generic', label: 'Generic' }
      ],
      disabled: true,
      conditional: {
        field: '_sourceNodeType',
        values: ['condition'],
        operator: 'equals'
      }
    },
    {
      type: 'select',
      name: 'contentType',
      label: 'Content Type',
      options: [
        { value: 'empty', label: 'Empty (Fixed)' }
      ],
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