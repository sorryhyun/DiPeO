
import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';

export const jsonSchemaValidatorSpec: NodeSpecification = {
  nodeType: NodeType.JSON_SCHEMA_VALIDATOR,
  displayName: "JSON Schema Validator",
  category: "codegen",
  icon: "✓",
  color: "#8BC34A",
  description: "Validate data against JSON schema",

  fields: [
    {
      name: "schema_path",
      type: "string",
      required: false,
      description: "Path to JSON schema file",
      uiConfig: {
        inputType: "text",
        placeholder: "/path/to/file"
      }
    },
    {
      name: "json_schema",
      type: "object",
      required: false,
      description: "Inline JSON schema",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "data_path",
      type: "string",
      required: false,
      description: "Data Path configuration",
      uiConfig: {
        inputType: "text",
        placeholder: "/path/to/file"
      }
    },
    {
      name: "strict_mode",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "Strict Mode configuration",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "error_on_extra",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "Error On Extra configuration",
      uiConfig: {
        inputType: "checkbox"
      }
    }
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
      description: "Data object to validate against the JSON schema"
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

  primaryDisplayField: "schema_path",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.json_schema_validator",
    className: "JsonSchemaValidatorHandler",
    mixins: ["LoggingMixin", "ValidationMixin"],
    serviceKeys: ["FILE_SYSTEM", "STATE_STORE"]
  }
};
