
import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';

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
      defaultValue: "",
      description: "API endpoint URL",
      uiConfig: {
        inputType: "text",
        placeholder: "https://example.com"
      }
    },
    {
      name: "method",
      type: "enum",
      required: true,
      defaultValue: "GET",
      description: "HTTP method",
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
      description: "HTTP headers",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "params",
      type: "object",
      required: false,
      description: "Query parameters",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "body",
      type: "object",
      required: false,
      description: "Request body",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "timeout",
      type: "number",
      required: false,
      description: "Request timeout in seconds",
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
      description: "Authentication type",
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
      description: "Authentication configuration",
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
      description: "API response data"
    }
  },

  execution: {
    timeout: 300,
    retryable: true,
    maxRetries: 3
  },

  primaryDisplayField: "method",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.api_job",
    className: "ApiJobHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["HTTP_CLIENT", "STATE_STORE"]
  }
};
