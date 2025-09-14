import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

// Shared field patterns as const objects
const RESULT_FIELDS = [
  { name: 'success' },
  { name: 'message' },
  { name: 'error' }
];

export const cliSessionQueries: EntityQueryDefinitions = {
  entity: 'CliSession',
  queries: [
    {
      name: 'RegisterCliSession',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'RegisterCliSessionInput', required: true }
      ],
      fields: [
        {
          name: 'register_cli_session',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: RESULT_FIELDS
        }
      ]
    },
    {
      name: 'UnregisterCliSession',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'UnregisterCliSessionInput', required: true }
      ],
      fields: [
        {
          name: 'unregister_cli_session',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: RESULT_FIELDS
        }
      ]
    }
  ]
};
