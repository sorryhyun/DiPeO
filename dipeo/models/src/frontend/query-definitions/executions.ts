import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const executionQueries: EntityQueryDefinitions = {
  entity: 'Execution',
  queries: [
    {
      name: 'GetExecution',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'execution',
          args: [
            { name: 'id', value: 'id', isVariable: true }
          ],
          fields: [
            { name: 'id' },
            { name: 'status' },
            { name: 'diagram_id' },
            { name: 'started_at' },
            { name: 'ended_at' },
            { name: 'error' },
            { name: 'node_states' },
            { name: 'node_outputs' },
            { name: 'variables' },
            { name: 'metrics' }
          ]
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
          fields: [
            { name: 'id' },
            { name: 'status' },
            { name: 'diagram_id' },
            { name: 'started_at' },
            { name: 'ended_at' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'ExecutionUpdates',
      type: QueryOperationType.SUBSCRIPTION,
      variables: [
        { name: 'execution_id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'execution_updates',
          args: [
            { name: 'execution_id', value: 'execution_id', isVariable: true }
          ],
          fields: [
            { name: 'execution_id' },
            { name: 'event_type' },
            { name: 'data' },
            { name: 'timestamp' }
          ]
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
              fields: [
                { name: 'id' },
                { name: 'status' }
              ]
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
          fields: [
            { name: 'success' },
            { name: 'message' },
            { name: 'error' }
          ]
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
              fields: [
                { name: 'id' },
                { name: 'status' }
              ]
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    }
  ]
};
