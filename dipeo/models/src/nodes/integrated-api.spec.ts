/**
 * Integrated API node specification
 * A unified node for all external API integrations
 */

import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';

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
      description: "API provider to connect to",
      // UI remains a select, but options are loaded dynamically in fieldOverrides
      uiConfig: {
        inputType: "select"
      }
    },
    {
      name: "operation",
      type: "string",
      required: true,
      description: "Operation to perform (provider-specific)",
      uiConfig: {
        inputType: "select",
        // Options will be dynamically populated based on provider
        placeholder: "Select an operation"
      }
    },
    {
      name: "resource_id",
      type: "string",
      required: false,
      description: "Resource identifier (e.g., page ID, channel ID)",
      uiConfig: {
        inputType: "text",
        placeholder: "Resource ID (if applicable)"
      }
    },
    {
      name: "config",
      type: "object",
      required: false,
      description: "Provider-specific configuration",
      uiConfig: {
        inputType: "code",
        placeholder: "{ /* provider-specific config */ }"
      }
    },
    {
      name: "timeout",
      type: "number",
      required: false,
      description: "Request timeout in seconds",
      validation: {
        min: 1,
        max: 300
      },
      uiConfig: {
        inputType: "number",
        placeholder: "30"
      }
    },
    {
      name: "max_retries",
      type: "number",
      required: false,
      description: "Maximum retry attempts",
      validation: {
        min: 0,
        max: 10
      },
      uiConfig: {
        inputType: "number",
        placeholder: "3"
      }
    }
  ],

  handles: {
    inputs: ["default"],
    outputs: ["default", "error"]
  },

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

  primaryDisplayField: "provider"
};
