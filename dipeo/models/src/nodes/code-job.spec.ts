
import { NodeType } from '../core/enums/node-types.js';
import { SupportedLanguage } from '../core/enums/node-specific.js';
import { NodeSpecification } from '../node-specification.js';
import { filePathField, contentField, textField, timeoutField } from '../core/field-presets.js';
import { validatedEnumField } from '../core/validation-utils.js';

export const codeJobSpec: NodeSpecification = {
  nodeType: NodeType.CODE_JOB,
  displayName: "Code Job",
  category: "compute",
  icon: "💻",
  color: "#9C27B0",
  description: "Execute custom code functions",

  fields: [
    validatedEnumField({
      name: "language",
      description: "Programming language",
      options: [
        { value: SupportedLanguage.PYTHON, label: "Python" },
        { value: SupportedLanguage.TYPESCRIPT, label: "TypeScript" },
        { value: SupportedLanguage.BASH, label: "Bash" },
        { value: SupportedLanguage.SHELL, label: "Shell" }
      ],
      defaultValue: SupportedLanguage.PYTHON,
      required: true
    }),
    filePathField({
      name: "file_path",
      description: "Path to code file"
    }),
    contentField({
      name: "code",
      description: "Inline code to execute (alternative to file_path)",
      inputType: "code",
      rows: 10
    }),
    textField({
      name: "function_name",
      description: "Function to execute"
    }),
    timeoutField()
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
      description: "Input data passed to the code function"
    },
    {
      name: "code",
      contentType: "raw_text",
      required: true,
      description: "Code to execute (overrides file_path if provided)"
    }
  ],

  outputs: {
    result: {
      type: "any",
      description: "Code execution result"
    }
  },

  execution: {
    timeout: 300,
    retryable: true,
    maxRetries: 3
  },

  primaryDisplayField: "language",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.code_job",
    className: "CodeJobHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["FILE_SYSTEM", "STATE_STORE"]
  }
};
