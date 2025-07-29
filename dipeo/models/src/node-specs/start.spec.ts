/**
 * Start node specification
 */

import { NodeType } from '../diagram.js';
import { NodeSpecification } from './node-specifications';

export const startSpec: NodeSpecification = {
  nodeType: NodeType.START,
  displayName: "Start Node",
  category: "control",
  icon: "🚀",
  color: "#4CAF50",
  description: "Entry point for diagram execution",
  
  fields: [
    {
      name: "trigger_mode",
      type: "enum",
      required: true,
      defaultValue: "none",
      description: "How this start node is triggered",
      validation: {
        allowedValues: ["none", "manual", "hook"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "none", label: "None - Simple start point" },
          { value: "manual", label: "Manual - Triggered manually with data" },
          { value: "hook", label: "Hook - Triggered by external events" }
        ]
      }
    },
    {
      name: "custom_data",
      type: "string",
      required: false,
      description: "Custom data to pass when manually triggered",
      conditional: {
        field: "trigger_mode",
        values: ["manual"]
      },
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "output_data_structure",
      type: "object",
      required: false,
      description: "Expected output data structure",
      conditional: {
        field: "trigger_mode",
        values: ["manual"]
      },
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "hook_event",
      type: "string",
      required: false,
      description: "Event name to listen for",
      conditional: {
        field: "trigger_mode",
        values: ["hook"]
      },
      uiConfig: {
        inputType: "text",
        placeholder: "e.g., webhook.received, file.uploaded"
      }
    },
    {
      name: "hook_filters",
      type: "object",
      required: false,
      description: "Filters to apply to incoming events",
      conditional: {
        field: "trigger_mode",
        values: ["hook"]
      },
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    }
  ],
  
  handles: {
    inputs: [],
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