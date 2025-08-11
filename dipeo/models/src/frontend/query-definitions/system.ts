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
          name: 'system_info',
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
          name: 'execution_capabilities',
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
          name: 'health',
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
          name: 'execution_order',
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
          name: 'execution_metrics',
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
          name: 'execution_history',
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
          name: 'active_cli_session',
          fields: [
            { name: 'execution_id' },
            { name: 'diagram_name' },
            { name: 'diagram_format' },
            { name: 'started_at' },
            { name: 'is_active' },
            { name: 'diagram_data' }
          ]
        }
      ]
    }
  ]
};