import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const diagramQueries: EntityQueryDefinitions = {
  entity: 'Diagram',
  queries: [
    {
      name: 'GetDiagram',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'diagram_id', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'diagram',
          args: [
            { name: 'diagram_id', value: 'diagram_id', isVariable: true }
          ],
          fields: [
            {
              name: 'nodes',
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
            {
              name: 'handles',
              fields: [
                { name: 'id' },
                { name: 'node_id' },
                { name: 'label' },
                { name: 'direction' },
                { name: 'data_type' },
                { name: 'position' }
              ]
            },
            {
              name: 'arrows',
              fields: [
                { name: 'id' },
                { name: 'source' },
                { name: 'target' },
                { name: 'content_type' },
                { name: 'label' },
                { name: 'data' }
              ]
            },
            {
              name: 'persons',
              fields: [
                { name: 'id' },
                { name: 'label' },
                {
                  name: 'llm_config',
                  fields: [
                    { name: 'service' },
                    { name: 'model' },
                    { name: 'api_key_id' },
                    { name: 'system_prompt' }
                  ]
                },
                { name: 'type' }
              ]
            },
            {
              name: 'metadata',
              fields: [
                { name: 'id' },
                { name: 'name' },
                { name: 'description' },
                { name: 'version' },
                { name: 'created' },
                { name: 'modified' },
                { name: 'author' },
                { name: 'tags' }
              ]
            }
          ]
        }
      ]
    },
    {
      name: 'ListDiagrams',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'filter', type: 'DiagramFilterInput' },
        { name: 'limit', type: 'Int' },
        { name: 'offset', type: 'Int' }
      ],
      fields: [
        {
          name: 'diagrams',
          args: [
            { name: 'filter', value: 'filter', isVariable: true },
            { name: 'limit', value: 'limit', isVariable: true },
            { name: 'offset', value: 'offset', isVariable: true }
          ],
          fields: [
            {
              name: 'metadata',
              fields: [
                { name: 'id' },
                { name: 'name' },
                { name: 'description' },
                { name: 'author' },
                { name: 'created' },
                { name: 'modified' },
                { name: 'tags' }
              ]
            },
            { name: 'nodeCount' },
            { name: 'arrowCount' }
          ]
        }
      ]
    },
    {
      name: 'CreateDiagram',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'CreateDiagramInput', required: true }
      ],
      fields: [
        {
          name: 'create_diagram',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            {
              name: 'diagram',
              fields: [
                {
                  name: 'metadata',
                  fields: [
                    { name: 'id' },
                    { name: 'name' }
                  ]
                }
              ]
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'ExecuteDiagram',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'ExecuteDiagramInput', required: true }
      ],
      fields: [
        {
          name: 'execute_diagram',
          args: [
            { name: 'input', value: 'input', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            {
              name: 'execution',
              fields: [
                { name: 'id' }
              ]
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'DeleteDiagram',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'diagram_id', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'delete_diagram',
          args: [
            { name: 'diagram_id', value: 'diagram_id', isVariable: true }
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
