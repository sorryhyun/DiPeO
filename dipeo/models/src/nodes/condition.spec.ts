
import { NodeType } from '../core/enums/node-types.js';
import { ConditionType } from '../core/enums/node-specific.js';
import { NodeSpecification } from '../node-specification.js';

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
      defaultValue: ConditionType.CUSTOM,
      description: "Type of condition to evaluate",
      validation: {
        allowedValues: ["detect_max_iterations", "check_nodes_executed", "custom", "llm_decision"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: ConditionType.DETECT_MAX_ITERATIONS, label: "Detect Max Iterations" },
          { value: ConditionType.CHECK_NODES_EXECUTED, label: "Check Nodes Executed" },
          { value: ConditionType.CUSTOM, label: "Custom Expression" },
          { value: ConditionType.LLM_DECISION, label: "LLM Decision" }
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
        values: [ConditionType.CUSTOM]
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
        values: [ConditionType.DETECT_MAX_ITERATIONS, ConditionType.CHECK_NODES_EXECUTED]
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
        values: [ConditionType.LLM_DECISION]
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
        values: [ConditionType.LLM_DECISION]
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
        values: [ConditionType.LLM_DECISION]
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
        values: [ConditionType.LLM_DECISION]
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
        values: [ConditionType.LLM_DECISION]
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

  inputPorts: [
    {
      name: "default",
      contentType: "object",
      required: false,
      description: "Input data for condition evaluation (object for custom expressions, conversation state for LLM decisions)"
    }
  ],

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

  primaryDisplayField: "condition_type",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.condition",
    className: "ConditionHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["LLM_CLIENT", "STATE_STORE", "EVENT_BUS"]
  }
};
