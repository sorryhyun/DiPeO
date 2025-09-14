import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

// Shared field patterns as const objects
const RESULT_FIELDS = [
  { name: 'success' },
  { name: 'message' },
  { name: 'error' }
];

const POSITION_FIELDS = [
  { name: 'x' },
  { name: 'y' }
];

const NODE_FIELDS = [
  { name: 'id' },
  { name: 'type' },
  {
    name: 'position',
    fields: POSITION_FIELDS
  },
  { name: 'data' }
];

export const nodeQueries: EntityQueryDefinitions = {
  entity: 'Node',
  queries: [
    {
      name: 'CreateNode',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'diagram_id', type: 'String', required: true },
        { name: 'input', type: 'CreateNodeInput', required: true }
      ],
      fields: [
        {
          name: 'create_node',
          args: [
            { name: 'diagram_id', value: 'diagram_id', isVariable: true },
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            {
              name: 'node',
              fields: NODE_FIELDS
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'UpdateNode',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'diagram_id', type: 'String', required: true },
        { name: 'node_id', type: 'String', required: true },
        { name: 'input', type: 'UpdateNodeInput', required: true }
      ],
      fields: [
        {
          name: 'update_node',
          args: [
            { name: 'diagram_id', value: 'diagram_id', isVariable: true },
            { name: 'node_id', value: 'node_id', isVariable: true },
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: RESULT_FIELDS
        }
      ]
    },
    {
      name: 'DeleteNode',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'diagram_id', type: 'String', required: true },
        { name: 'node_id', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'delete_node',
          args: [
            { name: 'diagram_id', value: 'diagram_id', isVariable: true },
            { name: 'node_id', value: 'node_id', isVariable: true }
          ],
          fields: RESULT_FIELDS
        }
      ]
    }
  ]
};
