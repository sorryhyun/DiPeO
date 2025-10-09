/**
 * Sub-Diagram node specification
 */

import { NodeType } from '../core/enums/node-types.js';
import { DiagramFormat } from '../core/enums/diagram.js';
import { NodeSpecification } from '../node-specification.js';
import { objectField, booleanField, textField } from '../core/field-presets.js';
import { validatedEnumField, validatedNumberField } from '../core/validation-utils.js';

export const subDiagramSpec: NodeSpecification = {
  nodeType: NodeType.SUB_DIAGRAM,
  displayName: "Sub-Diagram",
  category: "compute",
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
    objectField({
      name: "diagram_data",
      description: "Inline diagram data (alternative to diagram_name)",
      required: false,
      collapsible: true
    }),
    objectField({
      name: "input_mapping",
      description: "Map node inputs to sub-diagram variables",
      required: false
    }),
    objectField({
      name: "output_mapping",
      description: "Map sub-diagram outputs to node outputs",
      required: false
    }),
    validatedNumberField({
      name: "timeout",
      description: "Execution timeout in seconds",
      min: 1,
      max: 3600
    }),
    booleanField({
      name: "wait_for_completion",
      description: "Whether to wait for sub-diagram completion",
      defaultValue: true
    }),
    booleanField({
      name: "isolate_conversation",
      description: "Create isolated conversation context for sub-diagram",
      defaultValue: false
    }),
    booleanField({
      name: "ignore_if_sub",
      description: "Skip execution if this diagram is being run as a sub-diagram",
      defaultValue: false
    }),
    validatedEnumField({
      name: "diagram_format",
      description: "Format of the diagram file (yaml, json, or light)",
      options: [
        { label: "YAML", value: DiagramFormat.YAML },
        { label: "JSON", value: DiagramFormat.JSON },
        { label: "Light", value: DiagramFormat.LIGHT }
      ],
      required: false
    }),
    booleanField({
      name: "batch",
      description: "Execute sub-diagram in batch mode for multiple inputs",
      defaultValue: false
    }),
    textField({
      name: "batch_input_key",
      description: "Key in inputs containing the array of items for batch processing",
      defaultValue: "items",
      placeholder: "items"
    }),
    booleanField({
      name: "batch_parallel",
      description: "Execute batch items in parallel",
      defaultValue: true
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
      description: "Input data to pass to the sub-diagram (mapped via input_mapping configuration)"
    }
  ],

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

  primaryDisplayField: "diagram_name",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.sub_diagram",
    className: "SubDiagramHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["DIAGRAM_SERVICE", "STATE_STORE", "EVENT_BUS"]
  }
};
