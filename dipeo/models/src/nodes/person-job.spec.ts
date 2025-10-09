
import { NodeType } from '../core/enums/node-types.js';
import { NodeSpecification } from '../node-specification.js';
import type { PersonID } from '../core/diagram.js';
import {
  personField,
  promptWithFileField,
  numberField,
  memoryControlFields,
  contentField,
  textField,
  batchExecutionFields
} from '../core/field-presets.js';

export const personJobSpec: NodeSpecification = {
  nodeType: NodeType.PERSON_JOB,
  displayName: "Person Job",
  category: "ai",
  icon: "🤖",
  color: "#2196F3",
  description: "Execute tasks using AI language models",

  fields: [
    personField(),
    ...promptWithFileField({
      name: 'first_only_prompt',
      fileFieldName: 'first_prompt_file',
      description: 'Prompt used only on first execution',
      placeholder: 'Enter prompt template...'
    }),
    ...promptWithFileField(),
    numberField({
      name: 'max_iteration',
      description: 'Maximum execution iterations',
      defaultValue: 100,
      min: 1,
      required: true
    }),
    ...memoryControlFields({ includeIgnorePerson: true }),
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
    contentField({
      name: 'text_format',
      description: 'JSON schema or response format for structured outputs',
      placeholder: '{"type": "object", "properties": {...}}',
      rows: 6,
      inputType: 'textarea'
    }),
    textField({
      name: 'text_format_file',
      description: 'Path to Python file containing Pydantic models for structured outputs',
      placeholder: 'path/to/models.py',
      column: 2
    }),
    contentField({
      name: 'resolved_prompt',
      description: 'Pre-resolved prompt content from compile-time',
      rows: 4,
      inputType: 'textarea'
    }),
    contentField({
      name: 'resolved_first_prompt',
      description: 'Pre-resolved first prompt content from compile-time',
      rows: 4,
      inputType: 'textarea'
    }),
    ...batchExecutionFields(),
  ],

  handles: {
    inputs: ["default", "first"],
    outputs: ["default"]
  },

  inputPorts: [
    {
      name: "default",
      contentType: "conversation_state",
      required: false,
      description: "Main conversation context and input data for AI processing"
    },
    {
      name: "first",
      contentType: "conversation_state",
      required: false,
      description: "Initial conversation context for first iteration (overrides default on first run)"
    }
  ],

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

  primaryDisplayField: "person",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.person_job",
    className: "PersonJobHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["LLM_CLIENT", "STATE_STORE", "EVENT_BUS"],
    skipGeneration: true  // Already has custom handler
  }
};
