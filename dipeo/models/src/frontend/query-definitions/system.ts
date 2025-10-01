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
          name: 'getSystemInfo',
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
          name: 'getExecutionCapabilities',
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
          name: 'healthCheck',
          // Returns JSONScalar with dynamic fields
          fields: []
        }
      ]
    },
    {
      name: 'GetExecutionOrder',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'execution_id', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'getExecutionOrder',
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
        { name: 'execution_id', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'getExecutionMetrics',
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
        { name: 'diagram_id', type: 'String' },
        { name: 'limit', type: 'Float' },
        { name: 'include_metrics', type: 'Boolean' }
      ],
      fields: [
        {
          name: 'getExecutionHistory',
          args: [
            { name: 'diagram_id', value: 'diagram_id', isVariable: true },
            { name: 'limit', value: 'limit', isVariable: true },
            { name: 'include_metrics', value: 'include_metrics', isVariable: true }
          ],
          // Returns JSONScalar with dynamic fields
          fields: []
        }
      ]
    },
    {
      name: 'GetActiveCliSession',
      type: QueryOperationType.QUERY,
      fields: [
        {
          name: 'getActiveCliSession',
          // Returns JSONScalar with dynamic fields
          fields: []
        }
      ]
    }
  ]
};
