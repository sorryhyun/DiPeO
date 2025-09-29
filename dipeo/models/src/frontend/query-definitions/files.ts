import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

// Shared field patterns as const objects
const CONVERSION_RESULT_FIELDS = [
  { name: 'success' },
  { name: 'data' },
  { name: 'format' },
  { name: 'message' },
  { name: 'error' }
];

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
      fields: []
    },
    {
      name: 'UploadDiagram',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'file', type: 'Upload', required: true },
        { name: 'format', type: 'DiagramFormatGraphQL', required: true }
      ],
      fields: []
    },
    {
      name: 'ValidateDiagram',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'content', type: 'String', required: true },
        { name: 'format', type: 'DiagramFormatGraphQL', required: true }
      ],
      fields: []
    },
    {
      name: 'ConvertDiagramFormat',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'content', type: 'String', required: true },
        { name: 'from_format', type: 'DiagramFormatGraphQL', required: true },
        { name: 'to_format', type: 'DiagramFormatGraphQL', required: true }
      ],
      fields: CONVERSION_RESULT_FIELDS
    }
  ]
};
