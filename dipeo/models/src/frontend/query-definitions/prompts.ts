import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const promptQueries: EntityQueryDefinitions = {
  entity: 'Prompt',
  queries: [
    {
      name: 'ListPromptFiles',
      type: QueryOperationType.QUERY,
      variables: [],
      fields: [
        {
          name: 'prompt_files',
          // Returns List[JSONScalar] with dynamic fields
          fields: []
        }
      ]
    },
    {
      name: 'GetPromptFile',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'filename', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'prompt_file',
          args: [
            { name: 'filename', value: 'filename', isVariable: true }
          ],
          // Returns JSONScalar with dynamic fields
          fields: []
        }
      ]
    }
  ]
};