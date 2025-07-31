
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
      description: "Type of condition to evaluate",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "expression",
      type: "string",
      required: false,
      description: "Boolean expression to evaluate",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "node_indices",
      type: "array",
      required: false,
      description: "Node indices for condition evaluation",
      validation: {
        itemType: "string"
      },
      uiConfig: {
        inputType: "text"
      }
    }
  ],
  
  handles: {
    inputs: ["default"],
    outputs: ["condtrue", "condfalse"]
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
  },
  
  primaryDisplayField: "condition_type"
};