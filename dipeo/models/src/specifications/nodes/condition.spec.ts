
import { NodeType } from '../../core/enums/node-types.js';
import { ConditionType } from '../../core/enums/node-specific.js';
import { NodeSpecification } from '../types.js';

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
      type: "enum",
      required: false,
      defaultValue: "custom",
      description: "Type of condition to evaluate",
      validation: {
        allowedValues: ["detect_max_iterations", "check_nodes_executed", "custom"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "detect_max_iterations", label: "Detect Max Iterations" },
          { value: "check_nodes_executed", label: "Check Nodes Executed" },
          { value: "custom", label: "Custom Expression" }
        ]
      }
    },
    {
      name: "expression",
      type: "string",
      required: false,
      description: "Boolean expression to evaluate",
      conditional: {
        field: "condition_type",
        values: ["custom"]
      },
      uiConfig: {
        inputType: "textarea",
        placeholder: "e.g., inputs.value > 10",
        rows: 3
      }
    },
    {
      name: "node_indices",
      type: "array",
      required: false,
      description: "Node indices for detect_max_iteration condition",
      conditional: {
        field: "condition_type",
        values: ["detect_max_iterations", "check_nodes_executed"]
      },
      validation: {
        itemType: "string"
      },
      uiConfig: {
        inputType: "nodeSelect",
        placeholder: "Select nodes to monitor"
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