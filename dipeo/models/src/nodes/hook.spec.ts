
import { NodeType } from '../core/enums/node-types.js';
import { HookType } from '../core/enums/node-specific.js';
import { NodeSpecification } from '../node-specification.js';
import { textField } from '../core/field-presets.js';
import { validatedEnumField, validatedTextField, validatedNumberField } from '../core/validation-utils.js';

export const hookSpec: NodeSpecification = {
  nodeType: NodeType.HOOK,
  displayName: "Hook",
  category: "compute",
  icon: "🪝",
  color: "#9333ea",
  description: "Executes hooks at specific points in the diagram execution",

  fields: [
    validatedEnumField({
      name: "hook_type",
      description: "Type of hook to execute",
      options: [
        { value: HookType.SHELL, label: "Shell" },
        { value: HookType.HTTP, label: "HTTP" },
        { value: HookType.PYTHON, label: "Python" },
        { value: HookType.FILE, label: "File" }
      ],
      defaultValue: HookType.SHELL,
      required: true
    }),
    textField({
      name: "command",
      description: "Shell command to run (for shell hooks)",
      placeholder: "Command to execute"
    }),
    validatedTextField({
      name: "url",
      description: "Webhook URL (for HTTP hooks)",
      pattern: "^https?://.+",
      placeholder: "https://api.example.com/webhook"
    }),
    validatedNumberField({
      name: "timeout",
      description: "Execution timeout in seconds",
      min: 1,
      max: 300,
      defaultValue: 60
    }),
    validatedNumberField({
      name: "retry_count",
      description: "Number of retries on failure",
      min: 0,
      max: 5,
      defaultValue: 0
    })
  ],

  handles: {
    inputs: ["default"],
    outputs: ["success", "error"]
  },

  inputPorts: [
    {
      name: "default",
      contentType: "object",
      required: false,
      description: "Input data to pass to the hook execution (e.g., event payload, context data)"
    }
  ],

  outputs: {
    success: {
      type: "any",
      description: "Success output"
    },
    error: {
      type: "any",
      description: "Error output"
    }
  },

  execution: {
    timeout: 60,
    retryable: true,
    maxRetries: 3
  },

  examples: [
    {
      name: "Shell Hook",
      description: "Execute a shell command",
      configuration: {
        hook_type: HookType.SHELL,
        command: "echo 'Hook executed'",
        timeout: 30
      }
    },
    {
      name: "Webhook",
      description: "Call a webhook URL",
      configuration: {
        hook_type: HookType.HTTP,
        url: "https://api.example.com/webhook",
        timeout: 60,
        retry_count: 2
      }
    }
  ],

  primaryDisplayField: "hook_type",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.hook",
    className: "HookHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["HTTP_CLIENT", "STATE_STORE", "EVENT_BUS"],
    skipGeneration: true
  }
};
