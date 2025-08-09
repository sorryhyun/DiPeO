
import { NodeType } from '../../core/enums/node-types.js';
import { MemoryView } from '../../core/enums/memory.js';
import { MemoryProfile } from '../../core/enums/memory.js';
import { NodeSpecification } from '../types.js';

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
        column: 2
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
        column: 2
      }
    },
    {
      name: "max_iteration",
      type: "number",
      required: true,
      defaultValue: 1,
      description: "Maximum execution iterations",
      uiConfig: {
        inputType: "number",
        min: 1
      }
    },
    {
      name: "memory_profile",
      type: "enum",
      required: false,
      description: "Memory profile for conversation context",
      defaultValue: "FOCUSED",
      validation: {
        allowedValues: Object.values(MemoryProfile)
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "FULL", label: "Full 🧠 - No limits, see everything" },
          { value: "FOCUSED", label: "Focused 🎯 - Last 20 messages, conversation pairs" },
          { value: "MINIMAL", label: "Minimal 💭 - Last 5 messages, system + direct only" },
          { value: "GOLDFISH", label: "Goldfish 🐠 - Last 1-2 exchanges only" },
          { value: "CUSTOM", label: "Custom ⚙️ - Use memory_settings below" }
        ]
      }
    },
    {
      name: "tools",
      type: "string",
      required: false,
      description: "Tools available to the AI agent",
      defaultValue: "none",
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
      name: "memory_settings",
      type: "object",
      required: false,
      description: "Custom memory settings (when memory_profile is CUSTOM)",
      conditional: {
        field: "memory_profile",
        values: ["CUSTOM"]
      },
      nestedFields: [
        {
          name: "view",
          type: "enum",
          required: true,
          description: "Memory view type",
          validation: {
            allowedValues: ["FULL_CONVERSATION", "RELATED_CONVERSATION_PAIRS", "DIRECT_MESSAGES", "SYSTEM_AND_DIRECT"]
          },
          uiConfig: {
            inputType: "select",
            options: [
              { value: "FULL_CONVERSATION", label: "Full Conversation" },
              { value: "RELATED_CONVERSATION_PAIRS", label: "Related Conversation Pairs" },
              { value: "DIRECT_MESSAGES", label: "Direct Messages" },
              { value: "SYSTEM_AND_DIRECT", label: "System and Direct" }
            ]
          }
        },
        {
          name: "max_messages",
          type: "number",
          required: false,
          description: "Maximum number of messages to retain",
          uiConfig: {
            inputType: "number",
            min: 1,
            max: 100
          }
        },
        {
          name: "preserve_system",
          type: "boolean",
          required: false,
          description: "Always preserve system messages",
          defaultValue: true,
          uiConfig: {
            inputType: "checkbox"
          }
        }
      ],
      uiConfig: {
        inputType: "group",
        collapsible: true
      }
    }
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