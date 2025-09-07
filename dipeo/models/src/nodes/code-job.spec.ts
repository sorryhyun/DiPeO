
import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';

export const codeJobSpec: NodeSpecification = {
  nodeType: NodeType.CODE_JOB,
  displayName: "Code Job",
  category: "compute",
  icon: "💻",
  color: "#9C27B0",
  description: "Execute custom code functions",

  fields: [
    {
      name: "language",
      type: "enum",
      required: true,
      description: "Programming language",
      validation: {
        allowedValues: ["python", "typescript", "bash", "shell"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "python", label: "Python" },
          { value: "typescript", label: "TypeScript" },
          { value: "bash", label: "Bash" },
          { value: "shell", label: "Shell" }
        ]
      }
    },
    {
      name: "filePath",
      type: "string",
      required: false,
      description: "Path to code file",
      uiConfig: {
        inputType: "text",
        placeholder: "/path/to/file"
      }
    },
    {
      name: "code",
      type: "string",
      required: false,
      description: "Inline code to execute (alternative to filePath)",
      uiConfig: {
        inputType: "code",
        rows: 10,
        adjustable: true
      }
    },
    {
      name: "functionName",
      type: "string",
      required: false,
      description: "Function to execute",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "timeout",
      type: "number",
      required: false,
      description: "Execution timeout in seconds",
      uiConfig: {
        inputType: "number",
        min: 0,
        max: 3600
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
      description: "Input data passed to the code function"
    },
    {
      name: "code",
      contentType: "raw_text",
      required: true,
      description: "Code to execute (overrides filePath if provided)"
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

  primaryDisplayField: "language"
};
