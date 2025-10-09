
import { NodeType } from '../core/enums/node-types.js';
import { HookTriggerMode } from '../core/enums/node-specific.js';
import { NodeSpecification } from '../node-specification.js';

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
      required: false,
      defaultValue: HookTriggerMode.NONE,
      description: "How this start node is triggered",
      validation: {
        allowedValues: ["none", "manual", "hook"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: HookTriggerMode.NONE, label: "None - Simple start point" },
          { value: HookTriggerMode.MANUAL, label: "Manual - Triggered manually with data" },
          { value: HookTriggerMode.HOOK, label: "Hook - Triggered by external events" }
        ]
      }
    },
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
      name: "output_data_structure",
      type: "object",
      required: false,
      defaultValue: {},
      description: "Expected output data structure",
      conditional: {
        field: "trigger_mode",
        values: [HookTriggerMode.MANUAL]
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
        values: [HookTriggerMode.HOOK]
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
        values: [HookTriggerMode.HOOK]
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
