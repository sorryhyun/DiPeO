import type { UnifiedFieldDefinition } from '../field-registry';
import type { ArrowData } from '@/core/types';

interface ExtendedArrowData extends ArrowData {
  _sourceNodeType?: string;
}

export const arrowFields: UnifiedFieldDefinition<ExtendedArrowData>[] = [
  {
    name: 'label',
    type: 'text',
    label: 'Arrow Label',
    placeholder: 'e.g., user_query',
    column: 1,
    conditional: {
      field: '_sourceNodeType',
      values: ['condition'],
      operator: 'notEquals'
    }
  },
  {
    name: 'label',
    type: 'text',
    label: 'Arrow Label',
    placeholder: 'e.g., true, false, or custom label',
    column: 1,
    conditional: {
      field: '_sourceNodeType',
      values: ['condition'],
      operator: 'equals'
    }
  },
  {
    name: 'content_type',
    type: 'select',
    label: 'Content Type',
    column: 2,
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
    name: 'content_type',
    type: 'select',
    label: 'Content Type (Inherited from condition input)',
    column: 2,
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
    name: 'content_type',
    type: 'select',
    label: 'Content Type',
    column: 2,
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
    name: 'objectKeyPath',
    type: 'text',
    label: 'Object Key Path',
    placeholder: 'e.g., user.name or data.items[0].value',
    column: 1,
    conditional: {
      field: 'content_type',
      values: ['variable_in_object']
    }
  }
];