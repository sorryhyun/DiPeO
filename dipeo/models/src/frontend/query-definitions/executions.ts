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
          fields: [
            { name: 'id' },
            { name: 'status' },
            { name: 'phase' },
            { name: 'diagram_id' },
            { name: 'start_time' },
            { name: 'end_time' },
            { name: 'error' },
            {
              name: 'node_states',
              fields: [
                { name: 'node_id' },
                { name: 'status' },
                { name: 'start_time' },
                { name: 'end_time' },
                { name: 'error' },
                { name: 'outputs' }
              ]
            }
          ]
        }
      ]
    },
    {
      name: 'ListExecutions',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'diagram_id', type: 'ID' },
        { name: 'status', type: 'ExecutionStatus' },
        { name: 'limit', type: 'Int' },
        { name: 'offset', type: 'Int' }
      ],
      fields: [
        {
          name: 'executions',
          fields: [
            { name: 'id' },
            { name: 'status' },
            { name: 'phase' },
            { name: 'diagram_id' },
            { name: 'start_time' },
            { name: 'end_time' },
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
          fields: [
            { name: 'execution_id' },
            { name: 'status' },
            { name: 'phase' },
            { name: 'node_updates' },
            { name: 'timestamp' }
          ]
        }
      ]
    },
    {
      name: 'CancelExecution',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'cancel_execution',
          fields: [
            { name: 'success' },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    }
  ]
};