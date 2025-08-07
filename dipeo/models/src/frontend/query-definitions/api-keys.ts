import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const apiKeyQueries: EntityQueryDefinitions = {
  entity: 'ApiKey',
  queries: [
    {
      name: 'GetApiKeys',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'service', type: 'String' }
      ],
      fields: [
        {
          name: 'api_keys',
          fields: [
            { name: 'id' },
            { name: 'label' },
            { name: 'service' },
            { name: 'key' }
          ]
        }
      ]
    },
    {
      name: 'GetApiKey',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'api_key',
          fields: [
            { name: 'id' },
            { name: 'label' },
            { name: 'service' }
          ]
        }
      ]
    },
    {
      name: 'GetAvailableModels',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'service', type: 'String', required: true },
        { name: 'apiKeyId', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'available_models'
        }
      ]
    },
    {
      name: 'CreateApiKey',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'CreateApiKeyInput', required: true }
      ],
      fields: [
        {
          name: 'create_api_key',
          fields: [
            { name: 'success' },
            {
              name: 'api_key',
              fields: [
                { name: 'id' },
                { name: 'label' },
                { name: 'service' }
              ]
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'TestApiKey',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'test_api_key',
          fields: [
            { name: 'success' },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'DeleteApiKey',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'delete_api_key',
          fields: [
            { name: 'success' },
            { name: 'message' }
          ]
        }
      ]
    }
  ]
};