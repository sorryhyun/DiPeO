/**
 * JSON Schema Validator node specification
 */

import { NodeType } from '../diagram.js';
import { NodeSpecification } from '../node-specifications.js';

export const jsonSchemaValidatorSpec: NodeSpecification = {
  nodeType: NodeType.JSON_SCHEMA_VALIDATOR,
  displayName: "JSON Schema Validator",
  category: "validation",
  icon: "✓",
  color: "#8BC34A",
  description: "Validate data against JSON schema",
  
  fields: [
    {
      name: "schema_path",
      type: "string",
      required: false,
      description: "Schema Path configuration",
      uiConfig: {
        inputType: "text",
        placeholder: "/path/to/file"
      }
    },
    {
      name: "schema",
      type: "object",
      required: false,
      description: "Schema configuration",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "data_path",
      type: "string",
      required: false,
      description: "Data Path configuration",
      uiConfig: {
        inputType: "text",
        placeholder: "/path/to/file"
      }
    },
    {
      name: "strict_mode",
      type: "boolean",
      required: false,
      description: "Strict Mode configuration",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "error_on_extra",
      type: "boolean",
      required: false,
      description: "Error On Extra configuration",
      uiConfig: {
        inputType: "checkbox"
      }
    }
  ],
  
  handles: {
    inputs: ["in"],
    outputs: ["out"]
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
  }
};