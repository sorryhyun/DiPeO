import { NodeType } from '../core/enums/node-types.js';
import { DataType } from '../core/enums/data-types.js';
import { NodeSpecification } from '../node-specification.js';

export const irBuilderSpec: NodeSpecification = {
  nodeType: NodeType.IR_BUILDER,
  displayName: "IR Builder",
  category: "codegen",
  icon: "🏗️",
  color: "#FF5722",
  description: "Build Intermediate Representation for code generation",

  fields: [
    {
      name: "builder_type",
      type: "enum",
      required: true,
      description: "Type of IR builder to use",
      validation: {
        allowedValues: ["backend", "frontend", "strawberry", "custom"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "backend", label: "Backend" },
          { value: "frontend", label: "Frontend" },
          { value: "strawberry", label: "Strawberry (GraphQL)" },
          { value: "custom", label: "Custom" }
        ]
      }
    },
    {
      name: "source_type",
      type: "enum",
      required: false,
      description: "Type of source data",
      validation: {
        allowedValues: ["ast", "schema", "config", "auto"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "ast", label: "AST" },
          { value: "schema", label: "Schema" },
          { value: "config", label: "Config" },
          { value: "auto", label: "Auto-detect" }
        ]
      }
    },
    {
      name: "config_path",
      type: "string",
      required: false,
      description: "Path to configuration directory",
      uiConfig: {
        inputType: "text",
        placeholder: "projects/codegen/config/"
      }
    },
    {
      name: "output_format",
      type: "enum",
      required: false,
      description: "Output format for IR",
      validation: {
        allowedValues: ["json", "yaml", "python"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "json", label: "JSON" },
          { value: "yaml", label: "YAML" },
          { value: "python", label: "Python" }
        ]
      }
    },
    {
      name: "cache_enabled",
      type: "boolean",
      required: false,
      description: "Enable IR caching",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "validate_output",
      type: "boolean",
      required: false,
      description: "Validate IR structure before output",
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
      required: true,
      description: "Source data (AST, schema, or config) for IR generation"
    }
  ],

  outputs: {
    result: {
      type: DataType.OBJECT,
      description: "Generated IR structure"
    }
  },

  execution: {
    timeout: 120,
    retryable: true,
    maxRetries: 2
  },

  primaryDisplayField: "builder_type"
};
