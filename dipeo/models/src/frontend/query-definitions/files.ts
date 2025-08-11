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
        { name: 'file', type: 'Upload', required: true },
        { name: 'path', type: 'String' }
      ],
      fields: [
        {
          name: 'upload_file',
          args: [
            { name: 'file', value: 'file', isVariable: true },
            { name: 'path', value: 'path', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            { name: 'path' },
            { name: 'size_bytes' },
            { name: 'content_type' },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'UploadDiagram',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'file', type: 'Upload', required: true },
        { name: 'format', type: 'DiagramFormat', required: true }
      ],
      fields: [
        {
          name: 'upload_diagram',
          args: [
            { name: 'file', value: 'file', isVariable: true },
            { name: 'format', value: 'format', isVariable: true }
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
      name: 'ValidateDiagram',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'content', type: 'String', required: true },
        { name: 'format', type: 'DiagramFormat', required: true }
      ],
      fields: [
        {
          name: 'validate_diagram',
          args: [
            { name: 'content', value: 'content', isVariable: true },
            { name: 'format', value: 'format', isVariable: true }
          ],
          fields: [
            { name: 'success' },
            { name: 'errors' },
            { name: 'warnings' },
            { name: 'message' }
          ]
        }
      ]
    },
    {
      name: 'ConvertDiagramFormat',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'content', type: 'String', required: true },
        { name: 'from_format', type: 'DiagramFormat', required: true },
        { name: 'to_format', type: 'DiagramFormat', required: true }
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
            { name: 'content' },
            { name: 'format' },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    }
  ]
};