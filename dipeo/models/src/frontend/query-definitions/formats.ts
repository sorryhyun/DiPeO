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
          name: 'supported_formats',
          fields: [
            { name: 'format' },
            { name: 'name' },
            { name: 'description' },
            { name: 'extension' },
            { name: 'supports_import' },
            { name: 'supports_export' }
          ]
        }
      ]
    }
    // Note: Format conversion and validation are handled via file/diagram operations
  ]
};
