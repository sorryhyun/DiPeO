import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const fileQueries: EntityQueryDefinitions = {
  entity: 'File',
  queries: [
    // Note: File operations are handled through upload mutations
    // No direct file queries exist in the current schema
    {
      name: 'UploadFile',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'file', type: 'JSON', required: true },
        { name: 'path', type: 'String' }
      ],
      fields: [
        {
          name: 'upload_file',
          args: [
            { name: 'file', value: 'file', isVariable: true },
            { name: 'path', value: 'path', isVariable: true }
          ],
          fields: []
        }
      ]
    },
    {
      name: 'UploadDiagram',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'file', type: 'JSON', required: true },
        { name: 'format', type: 'DiagramFormatGraphQL', required: true }
      ],
      fields: [
        {
          name: 'upload_diagram',
          args: [
            { name: 'file', value: 'file', isVariable: true },
            { name: 'format', value: 'format', isVariable: true }
          ],
          fields: []
        }
      ]
    },
    {
      name: 'ValidateDiagram',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'content', type: 'String', required: true },
        { name: 'format', type: 'DiagramFormatGraphQL', required: true }
      ],
      fields: [
        {
          name: 'validate_diagram',
          args: [
            { name: 'content', value: 'content', isVariable: true },
            { name: 'format', value: 'format', isVariable: true }
          ],
          fields: []
        }
      ]
    },
    {
      name: 'ConvertDiagramFormat',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'content', type: 'String', required: true },
        { name: 'from_format', type: 'DiagramFormatGraphQL', required: true },
        { name: 'to_format', type: 'DiagramFormatGraphQL', required: true }
      ],
      fields: [
        {
          name: 'convert_diagram_format',
          args: [
            { name: 'content', value: 'content', isVariable: true },
            { name: 'from_format', value: 'from_format', isVariable: true },
            { name: 'to_format', value: 'to_format', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            { name: 'data' },
            { name: 'format' },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    }
  ]
};
