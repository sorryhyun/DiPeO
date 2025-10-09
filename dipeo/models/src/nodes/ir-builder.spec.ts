import { NodeType } from '../core/enums/node-types.js';
import { DataType } from '../core/enums/data-types.js';
import { IRBuilderTargetType, IRBuilderSourceType, IRBuilderOutputFormat } from '../core/enums/node-specific.js';
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
          { value: IRBuilderTargetType.BACKEND, label: "Backend" },
          { value: IRBuilderTargetType.FRONTEND, label: "Frontend" },
          { value: IRBuilderTargetType.STRAWBERRY, label: "Strawberry (GraphQL)" },
          { value: IRBuilderTargetType.CUSTOM, label: "Custom" }
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
          { value: IRBuilderSourceType.AST, label: "AST" },
          { value: IRBuilderSourceType.SCHEMA, label: "Schema" },
          { value: IRBuilderSourceType.CONFIG, label: "Config" },
          { value: IRBuilderSourceType.AUTO, label: "Auto-detect" }
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
          { value: IRBuilderOutputFormat.JSON, label: "JSON" },
          { value: IRBuilderOutputFormat.YAML, label: "YAML" },
          { value: IRBuilderOutputFormat.PYTHON, label: "Python" }
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

  primaryDisplayField: "builder_type",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.ir_builder",
    className: "IrBuilderHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["FILE_SYSTEM", "STATE_STORE"]
  }
};
