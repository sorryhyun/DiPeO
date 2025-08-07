import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const nodeQueries: EntityQueryDefinitions = {
  entity: 'Node',
  queries: [
    {
      name: 'GetNodeTypes',
      type: QueryOperationType.QUERY,
      fields: [
        {
          name: 'node_types'
        }
      ]
    },
    {
      name: 'GetNodeSpecification',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'type', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'node_specification',
          fields: [
            { name: 'type' },
            { name: 'label' },
            { name: 'category' },
            { name: 'description' },
            { name: 'input_handles' },
            { name: 'output_handles' },
            { name: 'properties' }
          ]
        }
      ]
    },
    {
      name: 'ValidateNode',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'ValidateNodeInput', required: true }
      ],
      fields: [
        {
          name: 'validate_node',
          fields: [
            { name: 'valid' },
            { name: 'errors' },
            { name: 'warnings' }
          ]
        }
      ]
    }
  ]
};