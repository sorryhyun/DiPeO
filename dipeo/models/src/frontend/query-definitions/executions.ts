import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

// Shared field patterns as const objects
const EXECUTION_FIELDS = [
  { name: 'id' },
  { name: 'status' },
  { name: 'diagram_id' },
  { name: 'started_at' },
  { name: 'ended_at' },
  { name: 'error' }
];

const EXECUTION_FIELDS_DETAILED = [
  { name: 'id' },
  { name: 'status' },
  { name: 'diagram_id' },
  { name: 'started_at' },
  { name: 'ended_at' },
  { name: 'error' },
  { name: 'node_states' },
  { name: 'node_outputs' },
  { name: 'variables' },
  { name: 'metrics' },
  {
    name: 'llm_usage',
    fields: [
      { name: 'input' },
      { name: 'output' },
      { name: 'cached' },
      { name: 'total' }
    ]
  }
];

const SUBSCRIPTION_UPDATE_FIELDS = [
  { name: 'execution_id' },
  { name: 'event_type' },
  { name: 'data' },
  { name: 'timestamp' }
];

const RESULT_FIELDS = [
  { name: 'success' },
  { name: 'message' },
  { name: 'error' }
];

const EXECUTION_WITH_STATUS_FIELDS = [
  { name: 'id' },
  { name: 'status' }
];

export const executionQueries: EntityQueryDefinitions = {
  entity: 'Execution',
  queries: [
    {
      name: 'GetExecution',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'execution_id', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'execution',
          args: [
            { name: 'execution_id', value: 'execution_id', isVariable: true }
          ],
          fields: EXECUTION_FIELDS_DETAILED
        }
      ]
    },
    {
      name: 'ListExecutions',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'filter', type: 'ExecutionFilterInput' },
        { name: 'limit', type: 'Int' },
        { name: 'offset', type: 'Int' }
      ],
      fields: [
        {
          name: 'executions',
          args: [
            { name: 'filter', value: 'filter', isVariable: true },
            { name: 'limit', value: 'limit', isVariable: true },
            { name: 'offset', value: 'offset', isVariable: true }
          ],
          fields: EXECUTION_FIELDS
        }
      ]
    },
    {
      name: 'ExecutionUpdates',
      type: QueryOperationType.SUBSCRIPTION,
      variables: [
        { name: 'execution_id', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'execution_updates',
          args: [
            { name: 'execution_id', value: 'execution_id', isVariable: true }
          ],
          fields: SUBSCRIPTION_UPDATE_FIELDS
        }
      ]
    },
    {
      name: 'ControlExecution',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'ExecutionControlInput', required: true }
      ],
      fields: [
        {
          name: 'control_execution',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            {
              name: 'execution',
              fields: EXECUTION_WITH_STATUS_FIELDS
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'SendInteractiveResponse',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'InteractiveResponseInput', required: true }
      ],
      fields: [
        {
          name: 'send_interactive_response',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: RESULT_FIELDS
        }
      ]
    },
    {
      name: 'UpdateNodeState',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'UpdateNodeStateInput', required: true }
      ],
      fields: [
        {
          name: 'update_node_state',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            {
              name: 'execution',
              fields: EXECUTION_WITH_STATUS_FIELDS
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    }
  ]
};
