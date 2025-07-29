/**
 * API Job node specification
 */

import { NodeType } from '../diagram.js';
import { NodeSpecification } from './node-specifications';

export const apiJobSpec: NodeSpecification = {
  nodeType: NodeType.API_JOB,
  displayName: "API Job",
  category: "integration",
  icon: "🌐",
  color: "#00BCD4",
  description: "Make HTTP API requests",
  
  fields: [
    {
      name: "url",
      type: "string",
      required: true,
      description: "Url configuration",
      uiConfig: {
        inputType: "text",
        placeholder: "https://example.com"
      }
    },
    {
      name: "method",
      type: "enum",
      required: true,
      description: "Method configuration",
      validation: {
        allowedValues: ["GET", "POST", "PUT", "DELETE", "PATCH"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "GET", label: "GET" },
          { value: "POST", label: "POST" },
          { value: "PUT", label: "PUT" },
          { value: "DELETE", label: "DELETE" },
          { value: "PATCH", label: "PATCH" }
        ]
      }
    },
    {
      name: "headers",
      type: "object",
      required: false,
      description: "Headers configuration",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "params",
      type: "object",
      required: false,
      description: "Params configuration",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "body",
      type: "object",
      required: false,
      description: "Body configuration",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "timeout",
      type: "number",
      required: false,
      description: "Timeout configuration",
      uiConfig: {
        inputType: "number",
        min: 0,
        max: 3600
      }
    },
    {
      name: "auth_type",
      type: "enum",
      required: false,
      description: "Auth Type configuration",
      validation: {
        allowedValues: ["none", "bearer", "basic", "api_key"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "none", label: "None" },
          { value: "bearer", label: "Bearer Token" },
          { value: "basic", label: "Basic Auth" },
          { value: "api_key", label: "API Key" }
        ]
      }
    },
    {
      name: "auth_config",
      type: "object",
      required: false,
      description: "Auth Config configuration",
      uiConfig: {
        inputType: "code",
        collapsible: true
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
  }
};