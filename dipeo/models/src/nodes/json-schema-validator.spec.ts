
import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';
import { filePathField, objectField, booleanField, textField } from '../core/field-presets.js';

export const jsonSchemaValidatorSpec: NodeSpecification = {
  nodeType: NodeType.JSON_SCHEMA_VALIDATOR,
  displayName: "JSON Schema Validator",
  category: "codegen",
  icon: "✓",
  color: "#8BC34A",
  description: "Validate data against JSON schema",

  fields: [
    filePathField({
      name: "schema_path",
      description: "Path to JSON schema file"
    }),
    objectField({
      name: "json_schema",
      description: "Inline JSON schema",
      required: false,
      collapsible: true
    }),
    textField({
      name: "data_path",
      description: "Data Path configuration",
      placeholder: "/path/to/file"
    }),
    booleanField({
      name: "strict_mode",
      description: "Strict Mode configuration",
      defaultValue: false
    }),
    booleanField({
      name: "error_on_extra",
      description: "Error On Extra configuration",
      defaultValue: false
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
