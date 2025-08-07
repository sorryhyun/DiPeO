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
          fields: [
            { name: 'version' },
            { name: 'environment' },
            { name: 'api_version' },
            { name: 'uptime' }
          ]
        }
      ]
    },
    {
      name: 'GetLLMServices',
      type: QueryOperationType.QUERY,
      fields: [
        {
          name: 'llm_services'
        }
      ]
    },
    {
      name: 'GetLLMModels',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'service', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'llm_models'
        }
      ]
    },
    {
      name: 'HealthCheck',
      type: QueryOperationType.QUERY,
      fields: [
        {
          name: 'health',
          fields: [
            { name: 'status' },
            { name: 'checks' }
          ]
        }
      ]
    }
  ]
};