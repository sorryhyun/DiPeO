
import { NodeType } from '../../core/enums/node-types.js';
import { NodeSpecification } from '../types.js';

export const dbSpec: NodeSpecification = {
  nodeType: NodeType.DB,
  displayName: "Database",
  category: "integration",
  icon: "🗄️",
  color: "#795548",
  description: "Database operations",

  fields: [
    {
      name: "file",
      type: "any",
      required: false,
      description: "File path or array of file paths",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "collection",
      type: "string",
      required: false,
      description: "Database collection name",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "sub_type",
      type: "enum",
      required: true,
      description: "Database operation type",
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
    },
    {
      name: "format",
      type: "string",
      required: false,
      description: "Data format (json, yaml, csv, text, etc.)",
      defaultValue: "json",
      uiConfig: {
        inputType: "select",
        options: [
          { value: "json", label: "JSON" },
          { value: "yaml", label: "YAML" },
          { value: "csv", label: "CSV" },
          { value: "text", label: "Text" },
          { value: "xml", label: "XML" }
        ]
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
