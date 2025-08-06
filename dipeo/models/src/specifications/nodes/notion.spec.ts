/**
 * Notion node specification
 */

import { NodeType } from '../../core/enums/node-types.js';
import { NodeSpecification } from '../types.js';

export const notionSpec: NodeSpecification = {
  nodeType: NodeType.NOTION,
  displayName: "Notion",
  category: "integration",
  icon: "📝",
  color: "#ec4899",
  description: "Integrate with Notion API to query, create, or update database entries",
  
  fields: [
    {
      name: "api_key",
      type: "string",
      required: true,
      description: "Notion API key for authentication",
      uiConfig: {
        inputType: "text",
        placeholder: "Your Notion API key"
      }
    },
    {
      name: "database_id",
      type: "string",
      required: true,
      description: "Notion database ID",
      uiConfig: {
        inputType: "text",
        placeholder: "Notion database ID"
      }
    },
    {
      name: "operation",
      type: "enum",
      required: true,
      description: "Operation to perform on the database",
      validation: {
        allowedValues: ["query_database", "create_page", "update_page", "read_page", "delete_page", "create_database", "update_database"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "query_database", label: "Query Database" },
          { value: "create_page", label: "Create Page" },
          { value: "update_page", label: "Update Page" },
          { value: "read_page", label: "Read Page" },
          { value: "delete_page", label: "Delete Page" },
          { value: "create_database", label: "Create Database" },
          { value: "update_database", label: "Update Database" }
        ]
      }
    },
    {
      name: "page_id",
      type: "string",
      required: false,
      description: "Page ID for update operations",
      uiConfig: {
        inputType: "text",
        placeholder: "Page ID (required for update)"
      }
    }
  ],
  
  handles: {
    inputs: ["default"],
    outputs: ["default"]
  },
  
  outputs: {
    result: {
      type: "any",
      description: "Notion API response"
    }
  },
  
  execution: {
    timeout: 30,
    retryable: true,
    maxRetries: 3
  },
  
  primaryDisplayField: "operation"
};