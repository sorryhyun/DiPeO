import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const conversationQueries: EntityQueryDefinitions = {
  entity: 'Conversation',
  queries: [
    {
      name: 'GetConversation',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'conversation',
          fields: [
            { name: 'id' },
            { name: 'title' },
            { name: 'created' },
            { name: 'updated' },
            {
              name: 'messages',
              fields: [
                { name: 'id' },
                { name: 'role' },
                { name: 'content' },
                { name: 'timestamp' }
              ]
            }
          ]
        }
      ]
    },
    {
      name: 'ListConversations',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'limit', type: 'Int' },
        { name: 'offset', type: 'Int' }
      ],
      fields: [
        {
          name: 'conversations',
          fields: [
            { name: 'id' },
            { name: 'title' },
            { name: 'created' },
            { name: 'updated' },
            { name: 'message_count' }
          ]
        }
      ]
    },
    {
      name: 'CreateConversation',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'CreateConversationInput', required: true }
      ],
      fields: [
        {
          name: 'create_conversation',
          fields: [
            { name: 'success' },
            {
              name: 'conversation',
              fields: [
                { name: 'id' },
                { name: 'title' }
              ]
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'AddMessage',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'conversationId', type: 'ID', required: true },
        { name: 'input', type: 'AddMessageInput', required: true }
      ],
      fields: [
        {
          name: 'add_message',
          fields: [
            { name: 'success' },
            {
              name: 'message',
              fields: [
                { name: 'id' },
                { name: 'role' },
                { name: 'content' },
                { name: 'timestamp' }
              ]
            },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'DeleteConversation',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'delete_conversation',
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