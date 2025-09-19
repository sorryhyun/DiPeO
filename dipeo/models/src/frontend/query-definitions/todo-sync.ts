import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

// Shared field patterns as const objects
const RESULT_FIELDS = [
  { name: 'success' },
  { name: 'message' },
  { name: 'error' },
  { name: 'data' }
];

const TODO_SYNC_CONFIG_FIELDS = [
  { name: 'mode' },
  { name: 'output_dir' },
  { name: 'auto_execute' },
  { name: 'monitor_enabled' },
  { name: 'debounce_seconds' }
];

const TODO_SYNC_STATUS_FIELDS = [
  { name: 'session_id' },
  { name: 'is_active' },
  { name: 'sync_count' },
  { name: 'last_sync' },
  { name: 'diagram_path' }
];

const TODO_DIAGRAM_FIELDS = [
  { name: 'id' },
  { name: 'name' },
  { name: 'session_id' },
  { name: 'originating_document' },
  { name: 'created_at' },
  { name: 'updated_at' },
  { name: 'todo_count' },
  { name: 'completed_count' },
  { name: 'in_progress_count' },
  { name: 'pending_count' },
  { name: 'last_sync' },
  { name: 'is_active' },
  { name: 'diagram_path' },
  { name: 'metadata', fields: [
    { name: 'trace_id' },
    { name: 'hook_timestamp' },
    { name: 'doc_path' }
  ]}
];

export const todoSyncQueries: EntityQueryDefinitions = {
  entity: 'TodoSync',
  queries: [
    {
      name: 'ToggleTodoSync',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'ToggleTodoSyncInput', required: true }
      ],
      fields: [
        {
          name: 'toggle_todo_sync',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ]
        }
      ]
    },
    {
      name: 'ConfigureTodoSync',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'ConfigureTodoSyncInput', required: true }
      ],
      fields: [
        {
          name: 'configure_todo_sync',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ]
        }
      ]
    },
    {
      name: 'TriggerTodoSync',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'session_id', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'trigger_todo_sync',
          args: [
            { name: 'session_id', value: 'session_id', isVariable: true }
          ]
        }
      ]
    },
    {
      name: 'GetTodoSyncStatus',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'session_id', type: 'String', required: false }
      ],
      fields: [
        {
          name: 'todo_sync_status',
          args: [
            { name: 'session_id', value: 'session_id', isVariable: true }
          ]
        }
      ]
    },
    {
      name: 'ListTodoDiagrams',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'session_id', type: 'String', required: false },
        { name: 'originating_document', type: 'String', required: false },
        { name: 'is_active', type: 'Boolean', required: false },
        { name: 'limit', type: 'Int', required: false },
        { name: 'offset', type: 'Int', required: false }
      ],
      fields: [
        {
          name: 'todo_diagrams',
          args: [
            { name: 'session_id', value: 'session_id', isVariable: true },
            { name: 'originating_document', value: 'originating_document', isVariable: true },
            { name: 'is_active', value: 'is_active', isVariable: true },
            { name: 'limit', value: 'limit', isVariable: true },
            { name: 'offset', value: 'offset', isVariable: true }
          ]
        }
      ]
    },
    {
      name: 'GetTodoDiagram',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'id', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'todo_diagram',
          args: [
            { name: 'id', value: 'id', isVariable: true }
          ]
        }
      ]
    },
    {
      name: 'SubscribeTodoUpdates',
      type: QueryOperationType.SUBSCRIPTION,
      variables: [
        { name: 'session_id', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'subscribe_todo_updates',
          args: [
            { name: 'session_id', value: 'session_id', isVariable: true }
          ]
        }
      ]
    }
  ]
};
