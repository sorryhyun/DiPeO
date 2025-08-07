import { EntityQueryDefinitions } from './types';
import { QueryOperationType } from '../query-enums';

export const promptQueries: EntityQueryDefinitions = {
  entity: 'Prompt',
  queries: [
    {
      name: 'GetPromptTemplates',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'category', type: 'String' }
      ],
      fields: [
        {
          name: 'prompt_templates',
          fields: [
            { name: 'id' },
            { name: 'name' },
            { name: 'category' },
            { name: 'description' },
            { name: 'template' },
            { name: 'variables' }
          ]
        }
      ]
    },
    {
      name: 'GetPromptTemplate',
      type: QueryOperationType.QUERY,
      variables: [
        { name: 'id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'prompt_template',
          fields: [
            { name: 'id' },
            { name: 'name' },
            { name: 'category' },
            { name: 'description' },
            { name: 'template' },
            { name: 'variables' },
            { name: 'examples' }
          ]
        }
      ]
    },
    {
      name: 'RenderPrompt',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'templateId', type: 'ID', required: true },
        { name: 'variables', type: 'JSON', required: true }
      ],
      fields: [
        {
          name: 'render_prompt',
          fields: [
            { name: 'success' },
            { name: 'rendered' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'CreatePromptTemplate',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'input', type: 'CreatePromptTemplateInput', required: true }
      ],
      fields: [
        {
          name: 'create_prompt_template',
          fields: [
            { name: 'success' },
            {
              name: 'template',
              fields: [
                { name: 'id' },
                { name: 'name' }
              ]
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'UpdatePromptTemplate',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'id', type: 'ID', required: true },
        { name: 'input', type: 'UpdatePromptTemplateInput', required: true }
      ],
      fields: [
        {
          name: 'update_prompt_template',
          fields: [
            { name: 'success' },
            {
              name: 'template',
              fields: [
                { name: 'id' },
                { name: 'name' }
              ]
            },
            { name: 'message' },
            { name: 'error' }
          ]
        }
      ]
    },
    {
      name: 'DeletePromptTemplate',
      type: QueryOperationType.MUTATION,
      variables: [
        { name: 'id', type: 'ID', required: true }
      ],
      fields: [
        {
          name: 'delete_prompt_template',
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