/**
 * Integrated API node specification
 * A unified node for all external API integrations
 */

import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';
import { textField, objectField } from '../core/field-presets.js';
import { validatedNumberField } from '../core/validation-utils.js';

export const integratedApiSpec: NodeSpecification = {
  nodeType: NodeType.INTEGRATED_API,
  displayName: "Integrated API",
  category: "integration",
  icon: "🔌",
  color: "#8b5cf6",
  description: "Connect to external APIs like Notion, Slack, GitHub, and more",

  fields: [
    {
      name: "provider",
      type: "string",
      required: true,
      defaultValue: "NOTION",
      description: "API provider to connect to",
      uiConfig: {
        inputType: "select"
      }
    },
    {
      name: "operation",
      type: "string",
      required: true,
      defaultValue: "",
      description: "Operation to perform (provider-specific)",
      uiConfig: {
        inputType: "select",
        placeholder: "Select an operation"
      }
    },
    textField({
      name: "resource_id",
      description: "Resource identifier (e.g., page ID, channel ID)",
      placeholder: "Resource ID (if applicable)"
    }),
    objectField({
      name: "config",
      description: "Provider-specific configuration",
      required: false
    }),
    validatedNumberField({
      name: "timeout",
      description: "Request timeout in seconds",
      min: 1,
      max: 300,
      defaultValue: 30,
      placeholder: "30"
    }),
    validatedNumberField({
      name: "max_retries",
      description: "Maximum retry attempts",
      min: 0,
      max: 10,
      defaultValue: 3,
      placeholder: "3"
    })
  ],

  handles: {
    inputs: ["default"],
    outputs: ["default", "error"]
  },

  inputPorts: [
    {
      name: "default",
      contentType: "object",
      required: false,
      description: "Input data for API request configuration (resource IDs, parameters, request body)"
    }
  ],

  outputs: {
    result: {
      type: "any",
      description: "API response data"
    },
    error: {
      type: "any",
      description: "Error details if the operation fails"
    }
  },

  execution: {
    timeout: 60,
    retryable: true,
    maxRetries: 3
  },

  primaryDisplayField: "provider",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.integrated_api",
    className: "IntegratedApiHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["HTTP_CLIENT", "STATE_STORE"]
  }
};
