
import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';

export const personJobSpec: NodeSpecification = {
  nodeType: NodeType.PERSON_JOB,
  displayName: "Person Job",
  category: "ai",
  icon: "🤖",
  color: "#2196F3",
  description: "Execute tasks using AI language models",

  fields: [
    {
      name: "person",
      type: "string",
      required: false,
      description: "AI person to use",
      uiConfig: {
        inputType: "personSelect"
      }
    },
    {
      name: "first_only_prompt",
      type: "string",
      required: true,
      description: "Prompt used only on first execution",
      uiConfig: {
        inputType: "textarea",
        placeholder: "Enter prompt template...",
        column: 2,
        rows: 10,
        adjustable: true,
        showPromptFileButton: true
      }
    },
    {
      name: "first_prompt_file",
      type: "string",
      required: false,
      description: "External prompt file for first iteration only",
      uiConfig: {
        inputType: "text",
        placeholder: "example_first.txt",
        column: 2,
        hidden: true
      }
    },
    {
      name: "default_prompt",
      type: "string",
      required: false,
      description: "Default prompt template",
      uiConfig: {
        inputType: "textarea",
        placeholder: "Enter prompt template...",
        column: 2,
        rows: 10,
        adjustable: true,
        showPromptFileButton: true
      }
    },
    {
      name: "prompt_file",
      type: "string",
      required: false,
      description: "Path to prompt file in /files/prompts/",
      uiConfig: {
        inputType: "text",
        placeholder: "example.txt",
        column: 2,
        hidden: true
      }
    },
    {
      name: "max_iteration",
      type: "number",
      required: true,
      defaultValue: 100,
      description: "Maximum execution iterations",
      uiConfig: {
        inputType: "number",
        min: 1
      }
    },
    {
      name: "memorize_to",
      type: "string",
      required: false,
      description: "Criteria used to select helpful messages for this task. Empty = memorize all. Special: 'GOLDFISH' for goldfish mode. Comma-separated for multiple criteria.",
      uiConfig: {
        inputType: "text",
        placeholder: "e.g., requirements, acceptance criteria, API keys",
        column: 2
      }
    },
    {
      name: "at_most",
      type: "number",
      required: false,
      description: "Select at most N messages to keep (system messages may be preserved in addition).",
      validation: {
        min: 1,
        max: 500
      },
      uiConfig: {
        inputType: "number",
        min: 1,
        max: 500,
        column: 1
      }
    },
    {
      name: "ignore_person",
      type: "string",
      required: false,
      description: "Comma-separated list of person IDs whose messages should be excluded from memory selection.",
      uiConfig: {
        inputType: "text",
        placeholder: "e.g., assistant, user2",
        column: 2
      }
    },
    {
      name: "tools",
      type: "string",
      required: false,
      description: "Tools available to the AI agent",
      uiConfig: {
        column: 1,
        inputType: "select",
        options: [
          { value: "none", label: "None - No tools" },
          { value: "image", label: "Image - Image generation capabilities" },
          { value: "websearch", label: "Web Search - Search the internet" }
        ]
      }
    },
    {
      name: "text_format",
      type: "string",
      required: false,
      description: "JSON schema or response format for structured outputs",
      uiConfig: {
        inputType: "textarea",
        placeholder: '{"type": "object", "properties": {...}}',
        column: 2,
        rows: 6,
        adjustable: true
      }
    },
    {
      name: "text_format_file",
      type: "string",
      required: false,
      description: "Path to Python file containing Pydantic models for structured outputs",
      uiConfig: {
        inputType: "text",
        placeholder: "path/to/models.py",
        column: 2
      }
    },
    // Internal fields for compile-time prompt resolution
    {
      name: "resolved_prompt",
      type: "string",
      required: false,
      description: "Pre-resolved prompt content from compile-time",
      uiConfig: {
        inputType: "textarea",
        column: 2,
        rows: 4
      }
    },
    {
      name: "resolved_first_prompt",
      type: "string",
      required: false,
      description: "Pre-resolved first prompt content from compile-time",
      uiConfig: {
        inputType: "textarea",
        column: 2,
        rows: 4
      }
    },
    // Batch execution fields
    {
      name: "batch",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "Enable batch mode for processing multiple items",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "batch_input_key",
      type: "string",
      required: false,
      defaultValue: "items",
      description: "Key containing the array to iterate over in batch mode",
      uiConfig: {
        inputType: "text",
        placeholder: "items"
      }
    },
    {
      name: "batch_parallel",
      type: "boolean",
      required: false,
      defaultValue: true,
      description: "Execute batch items in parallel",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "max_concurrent",
      type: "number",
      required: false,
      defaultValue: 10,
      description: "Maximum concurrent executions in batch mode",
      validation: {
        min: 1,
        max: 100
      },
      uiConfig: {
        inputType: "number",
        min: 1,
        max: 100
      }
    },
  ],

  handles: {
    inputs: ["default", "first"],
    outputs: ["default"]
  },

  outputs: {
    result: {
      type: "any",
      description: "AI response and results"
    }
  },

  execution: {
    timeout: 300,
    retryable: true,
    maxRetries: 3
  },

  primaryDisplayField: "person"
};
