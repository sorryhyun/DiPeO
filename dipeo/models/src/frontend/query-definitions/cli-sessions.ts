import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

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
          fields: [
            { name: 'success' },
            { name: 'session_id' },
            { name: 'message' },
            { name: 'error' }
          ]
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
          fields: [
            { name: 'success' },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    }
  ]
};