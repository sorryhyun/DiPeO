/**
 * Person Batch Job node specification
 */

import { NodeType } from '../../core/enums/node-types.js';
import { NodeSpecification } from '../types.js';

export const personBatchJobSpec: NodeSpecification = {
  nodeType: NodeType.PERSON_BATCH_JOB,
  displayName: "Person Batch Job",
  category: "ai",
  icon: "📦",
  color: "#8b5cf6",
  description: "Execute AI tasks on batches of data using language models",

  fields: [
    {
      name: "person",
      type: "string",
      required: false,
      description: "Person configuration for AI model",
      uiConfig: {
        inputType: "text",
        placeholder: "Select a person"
      }
    },
    {
      name: "batch_key",
      type: "string",
      required: true,
      description: "Key containing the array to iterate over",
      uiConfig: {
        inputType: "text",
        placeholder: "Key containing the array to iterate over"
      }
    },
    {
      name: "prompt",
      type: "string",
      required: true,
      description: "Prompt template for each batch item",
      validation: {
        minLength: 1
      },
      uiConfig: {
        inputType: "textarea",
        placeholder: "Use {{item}} for current batch item, {{variable_name}} for other variables",
        rows: 5,
        showPromptFileButton: true
      }
    }
  ],

  handles: {
    inputs: ["default"],
    outputs: ["default"]
  },

  outputs: {
    results: {
      type: "any",
      description: "Array of results from batch processing"
    }
  },

  execution: {
    timeout: 600,
    retryable: true,
    maxRetries: 3
  },

  primaryDisplayField: "batch_key"
};
