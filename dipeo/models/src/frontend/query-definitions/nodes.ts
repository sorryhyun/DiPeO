import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const nodeQueries: EntityQueryDefinitions = {
  entity: 'Node',
  queries: [
    {
      name: 'CreateNode',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'diagram_id', type: 'ID', required: true },
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
              fields: [
                { name: 'id' },
                { name: 'type' },
                {
                  name: 'position',
                  fields: [
                    { name: 'x' },
                    { name: 'y' }
                  ]
                },
                { name: 'data' }
              ]
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
        { name: 'diagram_id', type: 'ID', required: true },
        { name: 'node_id', type: 'ID', required: true },
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
          fields: [
            { name: 'success' },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'DeleteNode',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'diagram_id', type: 'ID', required: true },
        { name: 'node_id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'delete_node',
          args: [
            { name: 'diagram_id', value: 'diagram_id', isVariable: true },
            { name: 'node_id', value: 'node_id', isVariable: true }
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
