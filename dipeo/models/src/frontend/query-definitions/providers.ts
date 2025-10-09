import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

// Shared field patterns
const AUTH_CONFIG_FIELDS = [
  { name: 'strategy' },
  { name: 'header' },
  { name: 'query_param' },
  { name: 'format' },
  { name: 'scopes' }
];

const RATE_LIMIT_CONFIG_FIELDS = [
  { name: 'algorithm' },
  { name: 'capacity' },
  { name: 'refill_per_sec' },
  { name: 'window_size_sec' }
];

const RETRY_POLICY_FIELDS = [
  { name: 'strategy' },
  { name: 'max_retries' },
  { name: 'base_delay_ms' },
  { name: 'max_delay_ms' },
  { name: 'retry_on_status' }
];

const OPERATION_TYPE_FIELDS = [
  { name: 'name' },
  { name: 'method' },
  { name: 'path' },
  { name: 'description' },
  { name: 'required_scopes' },
  { name: 'has_pagination' },
  { name: 'timeout_override' }
];

const PROVIDER_METADATA_FIELDS = [
  { name: 'version' },
  { name: 'type' },
  { name: 'manifest_path' },
  { name: 'description' },
  { name: 'documentation_url' },
  { name: 'support_email' }
];

const PROVIDER_FIELDS = [
  { name: 'name' },
  {
    name: 'operations',
    fields: OPERATION_TYPE_FIELDS
  },
  {
    name: 'metadata',
    fields: PROVIDER_METADATA_FIELDS
  },
  { name: 'base_url' },
  {
    name: 'auth_config',
    fields: AUTH_CONFIG_FIELDS
  },
  {
    name: 'rate_limit',
    fields: RATE_LIMIT_CONFIG_FIELDS
  },
  {
    name: 'retry_policy',
    fields: RETRY_POLICY_FIELDS
  },
  { name: 'default_timeout' }
];

const OPERATION_SCHEMA_FIELDS = [
  { name: 'operation' },
  { name: 'method' },
  { name: 'path' },
  { name: 'description' },
  { name: 'request_body' },
  { name: 'query_params' },
  { name: 'response' }
];

const INTEGRATION_TEST_RESULT_FIELDS = [
  { name: 'success' },
  { name: 'provider' },
  { name: 'operation' },
  { name: 'status_code' },
  { name: 'response_time_ms' },
  { name: 'error' },
  { name: 'response_preview' }
];

export const providerQueries: EntityQueryDefinitions = {
  entity: 'Provider',
  queries: [
    {
      name: 'ListProviders',
      type: QueryOperationType.QUERY,
      variables: [],
      fields: [
        {
          name: 'listProviders',
          fields: PROVIDER_FIELDS
        }
      ]
    },
    {
      name: 'GetProvider',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'name', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'getProvider',
          args: [
            { name: 'name', value: 'name', isVariable: true }
          ],
          fields: PROVIDER_FIELDS
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
          name: 'getProviderOperations',
          args: [
            { name: 'provider', value: 'provider', isVariable: true }
          ],
          fields: []  // Returns JSON
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
          name: 'getOperationSchema',
          args: [
            { name: 'provider', value: 'provider', isVariable: true },
            { name: 'operation', value: 'operation', isVariable: true }
          ],
          fields: OPERATION_SCHEMA_FIELDS
        }
      ]
    },
    {
      name: 'GetProviderStatistics',
      type: QueryOperationType.QUERY,
      variables: [],
      fields: [
        {
          name: 'getProviderStatistics',
          fields: [
            { name: 'total_providers' },
            { name: 'total_operations' },
            { name: 'provider_types' },
            { name: 'providers' }
          ]
        }
      ]
    },
    {
      name: 'ExecuteIntegration',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'ExecuteIntegrationInput', required: true }
      ],
      fields: [
        {
          name: 'executeIntegration',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: []  // Returns JSON
        }
      ]
    },
    {
      name: 'TestIntegration',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'TestIntegrationInput', required: true }
      ],
      fields: [
        {
          name: 'testIntegration',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: INTEGRATION_TEST_RESULT_FIELDS
        }
      ]
    },
    {
      name: 'ReloadProvider',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'name', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'reloadProvider',
          args: [
            { name: 'name', value: 'name', isVariable: true }
          ],
          fields: []  // Returns JSON
        }
      ]
    }
  ]
};
