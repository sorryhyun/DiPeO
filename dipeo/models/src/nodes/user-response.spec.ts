
import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';
import { contentField, timeoutField } from '../core/field-presets.js';

export const userResponseSpec: NodeSpecification = {
  nodeType: NodeType.USER_RESPONSE,
  displayName: "User Response",
  category: "integration",
  icon: "💬",
  color: "#E91E63",
  description: "Collect user input",

  fields: [
    {
      ...contentField({
        name: "prompt",
        description: "Question to ask the user",
        placeholder: "Enter prompt template...",
        required: true
      }),
      defaultValue: ""
    },
    timeoutField({
      name: "timeout",
      description: "Response timeout in seconds",
      defaultValue: 60
    })
  ],

  handles: {
    inputs: ["default"],
    outputs: ["default"]
  },

  inputPorts: [
    {
      name: "default",
      contentType: "object",
      required: false,
      description: "Context data to display to the user along with the prompt"
    }
  ],

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

  primaryDisplayField: "prompt",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.user_response",
    className: "UserResponseHandler",
    mixins: ["LoggingMixin", "ValidationMixin"],
    serviceKeys: ["STATE_STORE", "EVENT_BUS"]
  }
};
