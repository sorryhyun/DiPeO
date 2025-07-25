/**
 * Start node specification
 */

import { NodeType } from '../diagram.js';
import { NodeSpecification } from '../node-specifications.js';

export const startSpec: NodeSpecification = {
  nodeType: NodeType.START,
  displayName: "Start Node",
  category: "control",
  icon: "🚀",
  color: "#4CAF50",
  description: "Entry point for diagram execution",
  
  fields: [
    {
      name: "custom_data",
      type: "string",
      required: true,
      description: "Custom Data configuration",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "output_data_structure",
      type: "object",
      required: true,
      description: "Output Data Structure configuration",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "trigger_mode",
      type: "enum",
      required: false,
      description: "Trigger Mode configuration",
      validation: {
        allowedValues: ["manual", "hook"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "manual", label: "Manual" },
          { value: "hook", label: "Hook" }
        ]
      }
    },
    {
      name: "hook_event",
      type: "string",
      required: false,
      description: "Hook Event configuration",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "hook_filters",
      type: "object",
      required: false,
      description: "Hook Filters configuration",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    }
  ],
  
  handles: {
    inputs: ["in"],
    outputs: ["out"]
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