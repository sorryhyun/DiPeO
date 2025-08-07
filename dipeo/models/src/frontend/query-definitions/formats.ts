import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const formatQueries: EntityQueryDefinitions = {
  entity: 'Format',
  queries: [
    {
      name: 'GetSupportedFormats',
      type: QueryOperationType.QUERY,
      fields: [
        {
          name: 'supported_formats'
        }
      ]
    },
    {
      name: 'ConvertFormat',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'ConvertFormatInput', required: true }
      ],
      fields: [
        {
          name: 'convert_format',
          fields: [
            { name: 'success' },
            { name: 'output' },
            { name: 'format' },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'ValidateFormat',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'ValidateFormatInput', required: true }
      ],
      fields: [
        {
          name: 'validate_format',
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