
import { NodeType } from '../../core/enums/node-types.js';
import { NodeSpecification } from '../types.js';

export const userResponseSpec: NodeSpecification = {
  nodeType: NodeType.USER_RESPONSE,
  displayName: "User Response",
  category: "integration",
  icon: "💬",
  color: "#E91E63",
  description: "Collect user input",
  
  fields: [
    {
      name: "prompt",
      type: "string",
      required: true,
      description: "Question to ask the user",
      uiConfig: {
        inputType: "textarea",
        placeholder: "Enter prompt template..."
      }
    },
    {
      name: "timeout",
      type: "number",
      required: false,
      defaultValue: 300,
      description: "Response timeout in seconds",
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
      description: "Node execution result"
    }
  },
  
  execution: {
    timeout: 300,
    retryable: true,
    maxRetries: 3
  },
  
  primaryDisplayField: "prompt"
};