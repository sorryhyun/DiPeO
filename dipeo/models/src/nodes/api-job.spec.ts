
import { NodeType } from '../core/enums/node-types.js';
import { HttpMethod } from '../core/enums/node-specific.js';
import { AuthType } from '../core/enums/integrations.js';
import { NodeSpecification } from '../node-specification.js';
import { textField, objectField, timeoutField } from '../core/field-presets.js';
import { validatedEnumField } from '../core/validation-utils.js';

export const apiJobSpec: NodeSpecification = {
  nodeType: NodeType.API_JOB,
  displayName: "API Job",
  category: "integration",
  icon: "🌐",
  color: "#00BCD4",
  description: "Make HTTP API requests",

  fields: [
    textField({
      name: "url",
      description: "API endpoint URL",
      placeholder: "https://example.com",
      required: true,
      defaultValue: ""
    }),
    validatedEnumField({
      name: "method",
      description: "HTTP method",
      options: [
        { value: HttpMethod.GET, label: "GET" },
        { value: HttpMethod.POST, label: "POST" },
        { value: HttpMethod.PUT, label: "PUT" },
        { value: HttpMethod.DELETE, label: "DELETE" },
        { value: HttpMethod.PATCH, label: "PATCH" }
      ],
      defaultValue: HttpMethod.GET,
      required: true
    }),
    objectField({
      name: "headers",
      description: "HTTP headers",
      required: false,
      collapsible: true
    }),
    objectField({
      name: "params",
      description: "Query parameters",
      required: false,
      collapsible: true
    }),
    objectField({
      name: "body",
      description: "Request body",
      required: false,
      collapsible: true
    }),
    timeoutField({
      name: "timeout",
      description: "Request timeout in seconds",
      required: false
    }),
    validatedEnumField({
      name: "auth_type",
      description: "Authentication type",
      options: [
        { value: AuthType.NONE, label: "None" },
        { value: AuthType.BEARER, label: "Bearer Token" },
        { value: AuthType.BASIC, label: "Basic Auth" },
        { value: AuthType.API_KEY, label: "API Key" }
      ],
      required: false
    }),
    objectField({
      name: "auth_config",
      description: "Authentication configuration",
      required: false,
      collapsible: true
    })
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
