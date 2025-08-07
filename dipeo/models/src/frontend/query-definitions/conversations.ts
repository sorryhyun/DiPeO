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
          // Pass all variables as arguments to the field
          args: [
            { name: 'person_id', value: 'person_id', isVariable: true },
            { name: 'execution_id', value: 'execution_id', isVariable: true },
            { name: 'search', value: 'search', isVariable: true },
            { name: 'show_forgotten', value: 'show_forgotten', isVariable: true },
            { name: 'limit', value: 'limit', isVariable: true },
            { name: 'offset', value: 'offset', isVariable: true },
            { name: 'since', value: 'since', isVariable: true }
          ],
          // Note: This returns JSONScalar, so fields are dynamic
          fields: []
        }
      ]
    }
  ]
};