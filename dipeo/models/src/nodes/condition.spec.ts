
import { NodeType } from '../core/enums/node-types.js';
import { ConditionType } from '../core/enums/node-specific.js';
import { NodeSpecification } from '../node-specification.js';
import type { PersonID } from '../core/diagram.js';
import { personField, contentField, textField, booleanField } from '../core/field-presets.js';
import { validatedEnumField, validatedArrayField, validatedNumberField } from '../core/validation-utils.js';

export const conditionSpec: NodeSpecification = {
  nodeType: NodeType.CONDITION,
  displayName: "Condition",
  category: "control",
  icon: "🔀",
  color: "#FF9800",
  description: "Conditional branching based on expressions",

  fields: [
    validatedEnumField({
      name: "condition_type",
      description: "Type of condition to evaluate",
      options: [
        { value: ConditionType.DETECT_MAX_ITERATIONS, label: "Detect Max Iterations" },
        { value: ConditionType.CHECK_NODES_EXECUTED, label: "Check Nodes Executed" },
        { value: ConditionType.CUSTOM, label: "Custom Expression" },
        { value: ConditionType.LLM_DECISION, label: "LLM Decision" }
      ],
      defaultValue: ConditionType.CUSTOM,
      required: false
    }),
    {
      ...contentField({
        name: "expression",
        description: "Boolean expression to evaluate",
        placeholder: "e.g., inputs.value > 10",
        rows: 3
      }),
      conditional: {
        field: "condition_type",
        values: [ConditionType.CUSTOM]
      }
    },
    validatedArrayField({
      name: "node_indices",
      description: "Node indices for detect_max_iteration condition",
      itemType: "string",
      inputType: "nodeSelect",
      placeholder: "Select nodes to monitor",
      conditional: {
        field: "condition_type",
        values: [ConditionType.DETECT_MAX_ITERATIONS, ConditionType.CHECK_NODES_EXECUTED]
      }
    }),
    {
      ...personField({
        description: "AI agent to use for decision making"
      }),
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
      ...contentField({
        name: "judge_by",
        description: "Prompt for LLM to make a judgment",
        placeholder: "Enter the prompt for LLM to judge (should result in YES/NO)",
        rows: 5
      }),
      conditional: {
        field: "condition_type",
        values: [ConditionType.LLM_DECISION]
      }
    },
    {
      ...textField({
        name: "judge_by_file",
        description: "External prompt file path",
        placeholder: "e.g., prompts/quality_check.txt"
      }),
      conditional: {
        field: "condition_type",
        values: [ConditionType.LLM_DECISION]
      }
    },
    {
      ...textField({
        name: "memorize_to",
        description: "Memory control strategy (e.g., GOLDFISH for fresh evaluation)",
        defaultValue: "GOLDFISH",
        placeholder: "e.g., GOLDFISH"
      }),
      conditional: {
        field: "condition_type",
        values: [ConditionType.LLM_DECISION]
      }
    },
    {
      ...validatedNumberField({
        name: "at_most",
        description: "Maximum messages to keep in memory",
        placeholder: "e.g., 10"
      }),
      conditional: {
        field: "condition_type",
        values: [ConditionType.LLM_DECISION]
      }
    },
    textField({
      name: "expose_index_as",
      description: "Variable name to expose the condition node's execution count (0-based index) to downstream nodes",
      placeholder: "e.g., current_index, loop_counter"
    }),
    booleanField({
      name: "skippable",
      description: "When true, downstream nodes can execute even if this condition hasn't been evaluated yet",
      defaultValue: false
    })
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
