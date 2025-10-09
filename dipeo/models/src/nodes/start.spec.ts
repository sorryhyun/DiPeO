
import { NodeType } from '../core/enums/node-types.js';
import { HookTriggerMode } from '../core/enums/node-specific.js';
import { NodeSpecification } from '../node-specification.js';
import { objectField, textField } from '../core/field-presets.js';
import { validatedEnumField } from '../core/validation-utils.js';

export const startSpec: NodeSpecification = {
  nodeType: NodeType.START,
  displayName: "Start Node",
  category: "control",
  icon: "🚀",
  color: "#4CAF50",
  description: "Entry point for diagram execution",

  fields: [
    validatedEnumField({
      name: "trigger_mode",
      description: "How this start node is triggered",
      options: [
        { value: HookTriggerMode.NONE, label: "None - Simple start point" },
        { value: HookTriggerMode.MANUAL, label: "Manual - Triggered manually with data" },
        { value: HookTriggerMode.HOOK, label: "Hook - Triggered by external events" }
      ],
      defaultValue: HookTriggerMode.NONE,
      required: false
    }),
    {
      name: "custom_data",
      type: "any",
      required: false,
      defaultValue: {},
      description: "Custom data to pass when manually triggered",
      conditional: {
        field: "trigger_mode",
        values: [HookTriggerMode.MANUAL]
      },
      uiConfig: {
        inputType: "text"
      }
    },
    {
      ...objectField({
        name: "output_data_structure",
        description: "Expected output data structure",
        required: false,
        collapsible: true
      }),
      defaultValue: {},
      conditional: {
        field: "trigger_mode",
        values: [HookTriggerMode.MANUAL]
      }
    },
    {
      ...textField({
        name: "hook_event",
        description: "Event name to listen for",
        placeholder: "e.g., webhook.received, file.uploaded"
      }),
      conditional: {
        field: "trigger_mode",
        values: [HookTriggerMode.HOOK]
      }
    },
    {
      ...objectField({
        name: "hook_filters",
        description: "Filters to apply to incoming events",
        required: false,
        collapsible: true
      }),
      conditional: {
        field: "trigger_mode",
        values: [HookTriggerMode.HOOK]
      }
    }
  ],

  handles: {
    inputs: [],
    outputs: ["default"]
  },

  inputPorts: [],

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
  },

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.start",
    className: "StartHandler",
    mixins: ["LoggingMixin", "ValidationMixin"],
    serviceKeys: ["STATE_STORE", "EVENT_BUS"]
  }
};
