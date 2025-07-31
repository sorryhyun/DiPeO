/**
 * Template Job node specification
 */

import { NodeType } from '../diagram.js';
import { NodeSpecification } from './node-specifications';

export const templateJobSpec: NodeSpecification = {
  nodeType: NodeType.TEMPLATE_JOB,
  displayName: "Template Job",
  category: "compute",
  icon: "📝",
  color: "#3F51B5",
  description: "Process templates with data",
  
  fields: [
    {
      name: "template_path",
      type: "string",
      required: false,
      description: "Template Path configuration",
      uiConfig: {
        inputType: "text",
        placeholder: "/path/to/file"
      }
    },
    {
      name: "template_content",
      type: "string",
      required: false,
      description: "Template Content configuration",
      uiConfig: {
        inputType: "text"
      }
    },
    {
      name: "output_path",
      type: "string",
      required: false,
      description: "Output Path configuration",
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
      description: "Engine configuration",
      validation: {
        allowedValues: ["internal", "jinja2", "handlebars"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "internal", label: "Internal" },
          { value: "jinja2", label: "Jinja2" },
          { value: "handlebars", label: "Handlebars" }
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
  
  primaryDisplayField: "template_name"
};