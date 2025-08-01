
import { NodeType } from '../diagram.js';
import { NodeSpecification } from './node-specifications';

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
      required: true,
      description: "Path to code file",
      uiConfig: {
        inputType: "text",
        placeholder: "/path/to/file"
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