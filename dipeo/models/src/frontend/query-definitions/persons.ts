import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const personQueries: EntityQueryDefinitions = {
  entity: 'Person',
  queries: [
    {
      name: 'GetPerson',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'person_id', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'person',
          args: [
            { name: 'person_id', value: 'person_id', isVariable: true }
          ],
          fields: [
            { name: 'id' },
            { name: 'label' },
            { name: 'type' },
            {
              name: 'llm_config',
              fields: [
                { name: 'service' },
                { name: 'model' },
                { name: 'api_key_id' },
                { name: 'system_prompt' }
              ]
            }
          ]
        }
      ]
    },
    {
      name: 'ListPersons',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'limit', type: 'Int' }
      ],
      fields: [
        {
          name: 'persons',
          args: [
            { name: 'limit', value: 'limit', isVariable: true }
          ],
          fields: [
            { name: 'id' },
            { name: 'label' },
            { name: 'type' },
            {
              name: 'llm_config',
              fields: [
                { name: 'service' },
                { name: 'model' },
                { name: 'api_key_id' }
              ]
            }
          ]
        }
      ]
    },
    {
      name: 'CreatePerson',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'CreatePersonInput', required: true }
      ],
      fields: [
        {
          name: 'create_person',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            {
              name: 'person',
              fields: [
                { name: 'id' },
                { name: 'label' }
              ]
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'UpdatePerson',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'person_id', type: 'String', required: true },
        { name: 'input', type: 'UpdatePersonInput', required: true }
      ],
      fields: [
        {
          name: 'update_person',
          args: [
            { name: 'person_id', value: 'person_id', isVariable: true },
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            {
              name: 'person',
              fields: [
                { name: 'id' },
                { name: 'label' }
              ]
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'DeletePerson',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'person_id', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'delete_person',
          args: [
            { name: 'person_id', value: 'person_id', isVariable: true }
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
