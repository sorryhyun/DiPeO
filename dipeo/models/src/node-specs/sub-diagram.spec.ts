/**
 * Sub-Diagram node specification
 */

import { NodeType } from '../diagram.js';
import { NodeSpecification } from './node-specifications';

export const subDiagramSpec: NodeSpecification = {
  nodeType: NodeType.SUB_DIAGRAM,
  displayName: "Sub-Diagram",
  category: "control",
  icon: "📊",
  color: "#8B5CF6",
  description: "Execute another diagram as a node within the current diagram",
  
  fields: [
    {
      name: "diagram_name",
      type: "string",
      required: false,
      description: "Name of the diagram to execute (e.g., 'workflow/process')",
      uiConfig: {
        inputType: "select",
        placeholder: "Select diagram..."
      }
    },
    {
      name: "diagram_data",
      type: "object",
      required: false,
      description: "Inline diagram data (alternative to diagram_name)",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "input_mapping",
      type: "object",
      required: false,
      description: "Map node inputs to sub-diagram variables",
      uiConfig: {
        inputType: "code",
        placeholder: "{ \"targetVar\": \"sourceInput\" }"
      }
    },
    {
      name: "output_mapping",
      type: "object",
      required: false,
      description: "Map sub-diagram outputs to node outputs",
      uiConfig: {
        inputType: "code",
        placeholder: "{ \"outputKey\": \"nodeId.field\" }"
      }
    },
    {
      name: "timeout",
      type: "number",
      required: false,
      description: "Execution timeout in seconds",
      validation: {
        min: 1,
        max: 3600
      },
      uiConfig: {
        inputType: "number",
        min: 1,
        max: 3600
      }
    },
    {
      name: "wait_for_completion",
      type: "boolean",
      required: false,
      defaultValue: true,
      description: "Whether to wait for sub-diagram completion",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "isolate_conversation",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "Create isolated conversation context for sub-diagram",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "ignoreIfSub",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "Skip execution if this diagram is being run as a sub-diagram",
      uiConfig: {
        inputType: "checkbox"
      }
    }
  ],
  
  handles: {
    inputs: ["default"],
    outputs: ["default"]
  },
  
  outputs: {
    default: {
      type: "any",
      description: "Output from sub-diagram execution (includes results and error if any)"
    }
  },
  
  execution: {
    timeout: 600,
    retryable: true,
    maxRetries: 1
  },
  
  examples: [
    {
      name: "Execute Named Diagram",
      description: "Execute a diagram by name with input mapping",
      configuration: {
        diagram_name: "codegen/node_ui_codegen",
        input_mapping: {
          spec_path: "node_specification",
          output_dir: "output_directory"
        },
        wait_for_completion: true
      }
    },
    {
      name: "Execute Inline Diagram",
      description: "Execute an inline diagram definition",
      configuration: {
        diagram_data: {
          nodes: [
            {
              id: "start",
              type: "start",
              data: {}
            }
          ],
          connections: []
        },
        timeout: 30
      }
    }
  ],
  
  primaryDisplayField: "diagram_name"
};