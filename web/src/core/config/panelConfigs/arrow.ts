import type { TypedPanelConfig, ArrowFormData } from '@/features/diagram-editor/types/panel';

interface ExtendedArrowFormData extends ArrowFormData {
  contentType?: string;
  objectKeyPath?: string;
  _sourceNodeType?: string;
}

export const arrowPanelConfig: TypedPanelConfig<ExtendedArrowFormData> = {
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
      label: 'Arrow Label',
      placeholder: 'e.g., true, false, or custom label',
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
    }
  ]
};