
import { NodeType } from '../core/enums/node-types.js';
import { HttpMethod } from '../core/enums/node-specific.js';
import { AuthType } from '../core/enums/integrations.js';
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
      defaultValue: HttpMethod.GET,
      description: "HTTP method",
      validation: {
        allowedValues: ["GET", "POST", "PUT", "DELETE", "PATCH"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: HttpMethod.GET, label: "GET" },
          { value: HttpMethod.POST, label: "POST" },
          { value: HttpMethod.PUT, label: "PUT" },
          { value: HttpMethod.DELETE, label: "DELETE" },
          { value: HttpMethod.PATCH, label: "PATCH" }
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
          { value: AuthType.NONE, label: "None" },
          { value: AuthType.BEARER, label: "Bearer Token" },
          { value: AuthType.BASIC, label: "Basic Auth" },
          { value: AuthType.API_KEY, label: "API Key" }
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

  inputPorts: [
    {
      name: "default",
      contentType: "object",
      required: false,
      description: "Input data for URL parameters, headers, or request body"
    }
  ],

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
