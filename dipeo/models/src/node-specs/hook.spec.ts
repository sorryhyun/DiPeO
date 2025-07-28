/**
 * Hook node specification
 */

import { NodeType } from '../diagram.js';
import { NodeSpecification } from './node-specifications';

export const hookSpec: NodeSpecification = {
  nodeType: NodeType.HOOK,
  displayName: "Hook",
  category: "control",
  icon: "🪝",
  color: "#9333ea",
  description: "Executes hooks at specific points in the diagram execution",
  
  fields: [
    {
      name: "hook_type",
      type: "enum",
      required: true,
      defaultValue: "shell",
      description: "Type of hook to execute",
      validation: {
        allowedValues: ["shell", "http", "python", "file"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "shell", label: "Shell" },
          { value: "http", label: "HTTP" },
          { value: "python", label: "Python" },
          { value: "file", label: "File" }
        ]
      }
    },
    {
      name: "command",
      type: "string",
      required: false,
      description: "Shell command to run (for shell hooks)",
      uiConfig: {
        inputType: "text",
        placeholder: "Command to execute"
      }
    },
    {
      name: "url",
      type: "string",
      required: false,
      description: "Webhook URL (for HTTP hooks)",
      validation: {
        pattern: "^https?://"
      },
      uiConfig: {
        inputType: "text",
        placeholder: "https://api.example.com/webhook"
      }
    },
    {
      name: "timeout",
      type: "number",
      required: false,
      defaultValue: 60,
      description: "Execution timeout in seconds",
      validation: {
        min: 1,
        max: 300
      },
      uiConfig: {
        inputType: "number",
        min: 1,
        max: 300
      }
    },
    {
      name: "retry_count",
      type: "number",
      required: false,
      defaultValue: 0,
      description: "Number of retries on failure",
      validation: {
        min: 0,
        max: 5
      },
      uiConfig: {
        inputType: "number",
        min: 0,
        max: 5
      }
    }
  ],
  
  handles: {
    inputs: ["trigger"],
    outputs: ["success", "error"]
  },
  
  outputs: {
    success: {
      type: "any",
      description: "Success output"
    },
    error: {
      type: "any",
      description: "Error output"
    }
  },
  
  execution: {
    timeout: 60,
    retryable: true,
    maxRetries: 3
  },
  
  examples: [
    {
      name: "Shell Hook",
      description: "Execute a shell command",
      configuration: {
        hook_type: "shell",
        command: "echo 'Hook executed'",
        timeout: 30
      }
    },
    {
      name: "Webhook",
      description: "Call a webhook URL",
      configuration: {
        hook_type: "http",
        url: "https://api.example.com/webhook",
        timeout: 60,
        retry_count: 2
      }
    }
  ]
};