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
          args: [
            { name: 'service', value: 'service', isVariable: true }
          ],
          fields: []
        }
      ]
    },
    {
      name: 'GetApiKey',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'api_key_id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'api_key',
          args: [
            { name: 'api_key_id', value: 'api_key_id', isVariable: true }
          ],
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
        { name: 'api_key_id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'available_models',
          args: [
            { name: 'service', value: 'service', isVariable: true },
            { name: 'api_key_id', value: 'api_key_id', isVariable: true }
          ]
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
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ],
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
        { name: 'api_key_id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'test_api_key',
          args: [
            { name: 'api_key_id', value: 'api_key_id', isVariable: true }
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
      name: 'DeleteApiKey',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'api_key_id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'delete_api_key',
          args: [
            { name: 'api_key_id', value: 'api_key_id', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            { name: 'message' }
          ]
        }
      ]
    }
  ]
};
