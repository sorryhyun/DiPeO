import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

// Shared field patterns as const objects
const POSITION_FIELDS = [
  { name: 'x' },
  { name: 'y' }
];

const LLM_CONFIG_FIELDS = [
  { name: 'service' },
  { name: 'model' },
  { name: 'api_key_id' },
  { name: 'system_prompt' }
];

const METADATA_FULL_FIELDS = [
  { name: 'id' },
  { name: 'name' },
  { name: 'description' },
  { name: 'version' },
  { name: 'created' },
  { name: 'modified' },
  { name: 'author' },
  { name: 'tags' }
];

const METADATA_COMPACT_FIELDS = [
  { name: 'id' },
  { name: 'name' },
  { name: 'description' },
  { name: 'author' },
  { name: 'created' },
  { name: 'modified' },
  { name: 'tags' }
];

const RESULT_FIELDS = [
  { name: 'success' },
  { name: 'message' },
  { name: 'error' }
];

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
                  fields: POSITION_FIELDS
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
                  fields: LLM_CONFIG_FIELDS
                },
                { name: 'type' }
              ]
            },
            {
              name: 'metadata',
              fields: METADATA_FULL_FIELDS
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
              fields: METADATA_COMPACT_FIELDS
            }
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
    },
    {
      name: 'ExecuteDiagram',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'ExecuteDiagramInput', required: true }
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
    },
    {
      name: 'DeleteDiagram',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'diagram_id', type: 'String', required: true }
      ],
      fields: RESULT_FIELDS
    }
  ]
};
