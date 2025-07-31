/**
 * Database node specification
 */

import { NodeType } from '../diagram.js';
import { NodeSpecification } from './node-specifications';

export const dbSpec: NodeSpecification = {
  nodeType: NodeType.DB,
  displayName: "Database",
  category: "data",
  icon: "🗄️",
  color: "#795548",
  description: "Database operations",
  
  fields: [
    {
      name: "file",
      type: "string",
      required: false,
      description: "File configuration (can be a single file path or array of file paths)",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "collection",
      type: "string",
      required: false,
      description: "Collection configuration",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "sub_type",
      type: "enum",
      required: true,
      description: "Sub Type configuration",
      validation: {
        allowedValues: ["fixed_prompt", "file", "code", "api_tool"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "fixed_prompt", label: "Fixed Prompt" },
          { value: "file", label: "File" },
          { value: "code", label: "Code" },
          { value: "api_tool", label: "API Tool" }
        ]
      }
    },
    {
      name: "operation",
      type: "string",
      required: true,
      description: "Operation configuration",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "query",
      type: "string",
      required: false,
      description: "Query configuration",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "data",
      type: "object",
      required: false,
      description: "Data configuration",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "serialize_json",
      type: "boolean",
      required: false,
      description: "Serialize structured data to JSON string (for backward compatibility)",
      defaultValue: false,
      uiConfig: {
        inputType: "checkbox"
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
      description: "Node execution result"
    }
  },
  
  execution: {
    timeout: 300,
    retryable: true,
    maxRetries: 3
  },
  
  primaryDisplayField: "operation"
};