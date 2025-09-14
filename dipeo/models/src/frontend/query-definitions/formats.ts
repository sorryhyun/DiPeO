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
          // Returns JSONScalar with dynamic fields
          fields: []
        }
      ]
    }
    // Note: Format conversion and validation are handled via file/diagram operations
  ]
};
