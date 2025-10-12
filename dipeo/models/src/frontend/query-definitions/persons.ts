import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

// Shared field patterns
const LLM_CONFIG_FULL = [
  { name: 'service' },
  { name: 'model' },
  { name: 'api_key_id' },
  { name: 'system_prompt' }
];

const LLM_CONFIG_COMPACT = [
  { name: 'service' },
  { name: 'model' },
  { name: 'api_key_id' }
];

const PERSON_DETAIL_FIELDS = [
  { name: 'id' },
  { name: 'label' },
  { name: 'type' },
  {
    name: 'llm_config',
    fields: LLM_CONFIG_FULL
  }
];

const PERSON_LIST_FIELDS = [
  { name: 'id' },
  { name: 'label' },
  { name: 'type' },
  {
    name: 'llm_config',
    fields: LLM_CONFIG_COMPACT
  }
];

const PERSON_COMPACT_FIELDS = [
  { name: 'id' },
  { name: 'label' }
];

const RESULT_FIELDS = [
  { name: 'success' },
  { name: 'message' },
  { name: 'error' }
];

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
          name: 'getPerson',
          args: [
            { name: 'person_id', value: 'person_id', isVariable: true }
          ],
          fields: PERSON_DETAIL_FIELDS
        }
      ]
    },
    {
      name: 'ListPersons',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'limit', type: 'Float' }
      ],
      fields: [
        {
          name: 'listPersons',
          args: [
            { name: 'limit', value: 'limit', isVariable: true }
          ],
          fields: PERSON_LIST_FIELDS
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
          name: 'createPerson',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            {
              name: 'data',
              fields: PERSON_COMPACT_FIELDS
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
          name: 'updatePerson',
          args: [
            { name: 'person_id', value: 'person_id', isVariable: true },
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            {
              name: 'data',
              fields: PERSON_COMPACT_FIELDS
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
          name: 'deletePerson',
          args: [
            { name: 'person_id', value: 'person_id', isVariable: true }
          ],
          fields: RESULT_FIELDS
        }
      ]
    }
  ]
};
