
import { NodeType } from '../core/enums/node-types.js';
import { TemplateEngine } from '../core/enums/node-specific.js';
import { NodeSpecification } from '../node-specification.js';
import { filePathField, contentField, objectField, textField } from '../core/field-presets.js';
import { validatedEnumField } from '../core/validation-utils.js';

export const templateJobSpec: NodeSpecification = {
  nodeType: NodeType.TEMPLATE_JOB,
  displayName: "Template Job",
  category: "codegen",
  icon: "📝",
  color: "#3F51B5",
  description: "Process templates with data",

  fields: [
    filePathField({
      name: "template_path",
      description: "Path to template file"
    }),
    contentField({
      name: "template_content",
      description: "Inline template content",
      placeholder: "Enter template content...",
      rows: 10
    }),
    filePathField({
      name: "output_path",
      description: "Output file path"
    }),
    objectField({
      name: "variables",
      description: "Variables configuration",
      required: false,
      collapsible: true
    }),
    validatedEnumField({
      name: "engine",
      description: "Template engine to use",
      options: [
        { value: TemplateEngine.INTERNAL, label: "Internal" },
        { value: TemplateEngine.JINJA2, label: "Jinja2" }
      ],
      defaultValue: TemplateEngine.JINJA2,
      required: false
    }),
    textField({
      name: "preprocessor",
      description: "Preprocessor function to apply before templating"
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
      description: "Template variables and data for template processing"
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

  primaryDisplayField: "engine",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.template_job",
    className: "TemplateJobHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["FILE_SYSTEM", "STATE_STORE"]
  }
};
