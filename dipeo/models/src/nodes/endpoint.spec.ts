
import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';
import { booleanField, textField } from '../core/field-presets.js';

export const endpointSpec: NodeSpecification = {
  nodeType: NodeType.ENDPOINT,
  displayName: "End Node",
  category: "control",
  icon: "🏁",
  color: "#F44336",
  description: "Exit point for diagram execution",

  fields: [
    booleanField({
      name: "save_to_file",
      description: "Save results to file",
      defaultValue: false
    }),
    textField({
      name: "file_name",
      description: "Output filename"
    })
  ],

  handles: {
    inputs: ["default"],
    outputs: []
  },

  inputPorts: [
    {
      name: "default",
      contentType: "object",
      required: false,
      description: "Final output data to be saved or returned from diagram execution"
    }
  ],

  outputs: {},

  execution: {
    timeout: 300,
    retryable: true,
    maxRetries: 3
  },

  primaryDisplayField: "save_to_file",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.endpoint",
    className: "EndpointHandler",
    mixins: ["LoggingMixin", "ValidationMixin"],
    serviceKeys: ["FILE_SYSTEM", "STATE_STORE", "EVENT_BUS"]
  }
};
