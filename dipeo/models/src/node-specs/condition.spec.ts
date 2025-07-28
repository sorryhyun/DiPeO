/**
 * Condition node specification
 */

import { NodeType } from '../diagram.js';
import { NodeSpecification } from './node-specifications';

export const conditionSpec: NodeSpecification = {
  nodeType: NodeType.CONDITION,
  displayName: "Condition",
  category: "control",
  icon: "🔀",
  color: "#FF9800",
  description: "Conditional branching based on expressions",
  
  fields: [
    {
      name: "condition_type",
      type: "string",
      required: true,
      description: "Condition Type configuration",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "expression",
      type: "string",
      required: false,
      description: "Expression configuration",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "node_indices",
      type: "array",
      required: false,
      description: "Node Indices configuration",
      validation: {
        itemType: "string"
      },
      uiConfig: {
        inputType: "text"
      }
    }
  ],
  
  handles: {
    inputs: ["in"],
    outputs: ["true", "false"]
  },
  
  outputs: {
    true: {
      type: "any",
      description: "Output when condition is true"
    },
    false: {
      type: "any",
      description: "Output when condition is false"
    }
  },
  
  execution: {
    timeout: 300,
    retryable: true,
    maxRetries: 3
  }
};