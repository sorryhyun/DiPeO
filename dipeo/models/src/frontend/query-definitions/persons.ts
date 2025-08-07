import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const personQueries: EntityQueryDefinitions = {
  entity: 'Person',
  queries: [
    {
      name: 'GetPerson',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'person',
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
                { name: 'system_prompt' },
                { name: 'temperature' }
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
        { name: 'filter', type: 'PersonFilterInput' },
        { name: 'limit', type: 'Int' },
        { name: 'offset', type: 'Int' }
      ],
      fields: [
        {
          name: 'persons',
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
        { name: 'id', type: 'ID', required: true },
        { name: 'input', type: 'UpdatePersonInput', required: true }
      ],
      fields: [
        {
          name: 'update_person',
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
        { name: 'id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'delete_person',
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