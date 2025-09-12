import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const providerQueries: EntityQueryDefinitions = {
  entity: 'Provider',
  queries: [
    {
      name: 'GetProviders',
      type: QueryOperationType.QUERY,
      variables: [],
      fields: [
        {
          name: 'providers',
          fields: [
            { name: 'name' },
            {
              name: 'operations',
              fields: [
                { name: 'name' },
                { name: 'method' },
                { name: 'path' },
                { name: 'description' },
                { name: 'required_scopes' }
              ]
            },
            {
              name: 'metadata',
              fields: [
                { name: 'version' },
                { name: 'type' },
                { name: 'description' },
                { name: 'documentation_url' }
              ]
            },
            { name: 'base_url' },
            { name: 'default_timeout' }
          ]
        }
      ]
    },
    {
      name: 'GetProviderOperations',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'provider', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'provider_operations',
          args: [
            { name: 'provider', value: 'provider', isVariable: true }
          ],
          fields: [
            { name: 'name' },
            { name: 'method' },
            { name: 'path' },
            { name: 'description' },
            { name: 'required_scopes' },
            { name: 'has_pagination' },
            { name: 'timeout_override' }
          ]
        }
      ]
    },
    {
      name: 'GetOperationSchema',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'provider', type: 'String', required: true },
        { name: 'operation', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'operation_schema',
          args: [
            { name: 'provider', value: 'provider', isVariable: true },
            { name: 'operation', value: 'operation', isVariable: true }
          ],
          fields: [
            { name: 'operation' },
            { name: 'method' },
            { name: 'path' },
            { name: 'description' },
            { name: 'request_body' },
            { name: 'query_params' },
            { name: 'response' }
          ]
        }
      ]
    }
  ]
};
