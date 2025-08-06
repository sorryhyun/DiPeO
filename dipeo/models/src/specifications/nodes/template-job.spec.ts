
import { NodeType } from '../../core/enums/node-types.js';
import { NodeSpecification } from '../types.js';

export const templateJobSpec: NodeSpecification = {
  nodeType: NodeType.TEMPLATE_JOB,
  displayName: "Template Job",
  category: "codegen",
  icon: "📝",
  color: "#3F51B5",
  description: "Process templates with data",
  
  fields: [
    {
      name: "template_path",
      type: "string",
      required: false,
      description: "Path to template file",
      uiConfig: {
        inputType: "text",
        placeholder: "/path/to/file"
      }
    },
    {
      name: "template_content",
      type: "string",
      required: false,
      description: "Inline template content",
      uiConfig: {
        inputType: "textarea",
        placeholder: "Enter template content...",
        rows: 10,
        adjustable: true
      }
    },
    {
      name: "output_path",
      type: "string",
      required: false,
      description: "Output file path",
      uiConfig: {
        inputType: "text",
        placeholder: "/path/to/file"
      }
    },
    {
      name: "variables",
      type: "object",
      required: false,
      description: "Variables configuration",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "engine",
      type: "enum",
      required: false,
      defaultValue: "jinja2",
      description: "Template engine to use",
      validation: {
        allowedValues: ["internal", "jinja2"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "internal", label: "Internal" },
          { value: "jinja2", label: "Jinja2" }
        ]
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
      description: "Node execution result"
    }
  },
  
  execution: {
    timeout: 300,
    retryable: true,
    maxRetries: 3
  },
  
  primaryDisplayField: "engine"
};