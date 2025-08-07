import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const fileQueries: EntityQueryDefinitions = {
  entity: 'File',
  queries: [
    {
      name: 'ListFiles',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'path', type: 'String' }
      ],
      fields: [
        {
          name: 'files',
          fields: [
            { name: 'name' },
            { name: 'path' },
            { name: 'size' },
            { name: 'modified' },
            { name: 'is_directory' }
          ]
        }
      ]
    },
    {
      name: 'GetFile',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'path', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'file',
          fields: [
            { name: 'name' },
            { name: 'path' },
            { name: 'content' },
            { name: 'size' },
            { name: 'modified' }
          ]
        }
      ]
    },
    {
      name: 'CreateFile',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'path', type: 'String', required: true },
        { name: 'content', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'create_file',
          fields: [
            { name: 'success' },
            {
              name: 'file',
              fields: [
                { name: 'path' },
                { name: 'size' }
              ]
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'UpdateFile',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'path', type: 'String', required: true },
        { name: 'content', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'update_file',
          fields: [
            { name: 'success' },
            {
              name: 'file',
              fields: [
                { name: 'path' },
                { name: 'size' },
                { name: 'modified' }
              ]
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'DeleteFile',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'path', type: 'String', required: true }
      ],
      fields: [
        {
          name: 'delete_file',
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