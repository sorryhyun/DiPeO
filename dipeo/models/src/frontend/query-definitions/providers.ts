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
          // Returns JSONScalar with dynamic fields
          fields: []
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
          // Returns JSONScalar with dynamic fields
          fields: []
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
          // Returns JSONScalar with dynamic fields
          fields: []
        }
      ]
    }
  ]
};
