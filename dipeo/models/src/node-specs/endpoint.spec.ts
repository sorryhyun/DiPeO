/**
 * Endpoint node specification
 */

import { NodeType } from '../diagram.js';
import { NodeSpecification } from './node-specifications';

export const endpointSpec: NodeSpecification = {
  nodeType: NodeType.ENDPOINT,
  displayName: "End Node",
  category: "control",
  icon: "🏁",
  color: "#F44336",
  description: "Exit point for diagram execution",
  
  fields: [
    {
      name: "save_to_file",
      type: "boolean",
      required: true,
      description: "Save To File configuration",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "file_name",
      type: "string",
      required: false,
      description: "File Name configuration",
      uiConfig: {
        inputType: "text"
      }
    }
  ],
  
  handles: {
    inputs: ["in"],
    outputs: []
  },
  
  outputs: {},
  
  execution: {
    timeout: 300,
    retryable: true,
    maxRetries: 3
  }
};