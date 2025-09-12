import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const systemQueries: EntityQueryDefinitions = {
  entity: 'System',
  queries: [
    {
      name: 'GetSystemInfo',
      type: QueryOperationType.QUERY,
      fields: [
        {
          name: 'get_system_info',
          // Returns JSONScalar with dynamic fields
          fields: []
        }
      ]
    },
    {
      name: 'GetExecutionCapabilities',
      type: QueryOperationType.QUERY,
      fields: [
        {
          name: 'get_execution_capabilities',
          // Returns JSONScalar with dynamic fields
          fields: []
        }
      ]
    },
    {
      name: 'HealthCheck',
      type: QueryOperationType.QUERY,
      fields: [
        {
          name: 'health_check',
          // Returns JSONScalar with dynamic fields
          fields: []
        }
      ]
    },
    {
      name: 'GetExecutionOrder',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'execution_id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'get_execution_order',
          args: [
            { name: 'execution_id', value: 'execution_id', isVariable: true }
          ],
          // Returns JSONScalar with dynamic fields
          fields: []
        }
      ]
    },
    {
      name: 'GetExecutionMetrics',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'execution_id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'get_execution_metrics',
          args: [
            { name: 'execution_id', value: 'execution_id', isVariable: true }
          ],
          // Returns JSONScalar with dynamic fields
          fields: []
        }
      ]
    },
    {
      name: 'GetExecutionHistory',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'diagram_id', type: 'ID' },
        { name: 'limit', type: 'Int' },
        { name: 'include_metrics', type: 'Boolean' }
      ],
      fields: [
        {
          name: 'get_execution_history',
          fields: [
            { name: 'id' },
            { name: 'status' },
            { name: 'diagram_id' },
            { name: 'started_at' },
            { name: 'ended_at' },
            { name: 'error' },
            { name: 'metrics' }
          ]
        }
      ]
    },
    {
      name: 'GetActiveCliSession',
      type: QueryOperationType.QUERY,
      fields: [
        {
          name: 'get_active_cli_session',
          fields: [
            { name: 'session_id' },
            { name: 'execution_id' },
            { name: 'diagram_name' },
            { name: 'diagram_format' },
            { name: 'started_at' },
            { name: 'is_active' },
            { name: 'diagram_data' },
            { name: 'node_states' }
          ]
        }
      ]
    }
  ]
};
