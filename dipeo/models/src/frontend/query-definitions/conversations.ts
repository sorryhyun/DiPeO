import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const conversationQueries: EntityQueryDefinitions = {
  entity: 'Conversation',
  queries: [
    {
      name: 'ListConversations',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'person_id', type: 'ID' },
        { name: 'execution_id', type: 'ID' },
        { name: 'search', type: 'String' },
        { name: 'show_forgotten', type: 'Boolean' },
        { name: 'limit', type: 'Int' },
        { name: 'offset', type: 'Int' },
        { name: 'since', type: 'DateTime' }
      ],
      fields: [
        {
          name: 'conversations',
          // Note: This returns JSONScalar, so fields are dynamic
          fields: []
        }
      ]
    }
  ]
};