import { NodeType } from '../core/enums/node-types.js';
import { DataType } from '../core/enums/data-types.js';
import { IRBuilderTargetType, IRBuilderSourceType, IRBuilderOutputFormat } from '../core/enums/node-specific.js';
import { NodeSpecification } from '../node-specification.js';
import { textField, booleanField } from '../core/field-presets.js';
import { validatedEnumField } from '../core/validation-utils.js';

export const irBuilderSpec: NodeSpecification = {
  nodeType: NodeType.IR_BUILDER,
  displayName: "IR Builder",
  category: "codegen",
  icon: "🏗️",
  color: "#FF5722",
  description: "Build Intermediate Representation for code generation",

  fields: [
    validatedEnumField({
      name: "builder_type",
      description: "Type of IR builder to use",
      options: [
        { value: IRBuilderTargetType.BACKEND, label: "Backend" },
        { value: IRBuilderTargetType.FRONTEND, label: "Frontend" },
        { value: IRBuilderTargetType.STRAWBERRY, label: "Strawberry (GraphQL)" },
        { value: IRBuilderTargetType.CUSTOM, label: "Custom" }
      ],
      required: true
    }),
    validatedEnumField({
      name: "source_type",
      description: "Type of source data",
      options: [
        { value: IRBuilderSourceType.AST, label: "AST" },
        { value: IRBuilderSourceType.SCHEMA, label: "Schema" },
        { value: IRBuilderSourceType.CONFIG, label: "Config" },
        { value: IRBuilderSourceType.AUTO, label: "Auto-detect" }
      ],
      required: false
    }),
    textField({
      name: "config_path",
      description: "Path to configuration directory",
      placeholder: "projects/codegen/config/"
    }),
    validatedEnumField({
      name: "output_format",
      description: "Output format for IR",
      options: [
        { value: IRBuilderOutputFormat.JSON, label: "JSON" },
        { value: IRBuilderOutputFormat.YAML, label: "YAML" },
        { value: IRBuilderOutputFormat.PYTHON, label: "Python" }
      ],
      required: false
    }),
    booleanField({
      name: "cache_enabled",
      description: "Enable IR caching"
    }),
    booleanField({
      name: "validate_output",
      description: "Validate IR structure before output"
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
