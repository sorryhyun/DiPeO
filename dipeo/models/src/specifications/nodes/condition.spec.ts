
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
        allowedValues: ["detect_max_iterations", "check_nodes_executed", "custom", "llm_decision"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "detect_max_iterations", label: "Detect Max Iterations" },
          { value: "check_nodes_executed", label: "Check Nodes Executed" },
          { value: "custom", label: "Custom Expression" },
          { value: "llm_decision", label: "LLM Decision" }
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
    },
    {
      name: "person",
      type: "string",
      required: false,
      description: "AI agent to use for decision making",
      conditional: {
        field: "condition_type",
        values: ["llm_decision"]
      },
      uiConfig: {
        inputType: "personSelect",
        placeholder: "Select AI agent"
      }
    },
    {
      name: "judge_by",
      type: "string",
      required: false,
      description: "Prompt for LLM to make a judgment",
      conditional: {
        field: "condition_type",
        values: ["llm_decision"]
      },
      uiConfig: {
        inputType: "textarea",
        placeholder: "Enter the prompt for LLM to judge (should result in YES/NO)",
        rows: 5
      }
    },
    {
      name: "judge_by_file",
      type: "string",
      required: false,
      description: "External prompt file path",
      conditional: {
        field: "condition_type",
        values: ["llm_decision"]
      },
      uiConfig: {
        inputType: "text",
        placeholder: "e.g., prompts/quality_check.txt"
      }
    },
    {
      name: "memorize_to",
      type: "string",
      required: false,
      defaultValue: "GOLDFISH",
      description: "Memory control strategy (e.g., GOLDFISH for fresh evaluation)",
      conditional: {
        field: "condition_type",
        values: ["llm_decision"]
      },
      uiConfig: {
        inputType: "text",
        placeholder: "e.g., GOLDFISH"
      }
    },
    {
      name: "at_most",
      type: "number",
      required: false,
      description: "Maximum messages to keep in memory",
      conditional: {
        field: "condition_type",
        values: ["llm_decision"]
      },
      uiConfig: {
        inputType: "number",
        placeholder: "e.g., 10"
      }
    },
    {
      name: "expose_index_as",
      type: "string",
      required: false,
      description: "Variable name to expose the condition node's execution count (0-based index) to downstream nodes",
      uiConfig: {
        inputType: "text",
        placeholder: "e.g., current_index, loop_counter"
      }
    },
    {
      name: "skippable",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "When true, downstream nodes can execute even if this condition hasn't been evaluated yet",
      uiConfig: {
        inputType: "checkbox"
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
