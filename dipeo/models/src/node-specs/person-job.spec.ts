/**
 * Person Job node specification
 */

import { NodeType, MemoryView } from '../diagram.js';
import { NodeSpecification } from './node-specifications';

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
      description: "Person configuration",
      uiConfig: {
        inputType: "personSelect"
      }
    },
    {
      name: "first_only_prompt",
      type: "string",
      required: true,
      description: "First Only Prompt configuration",
      uiConfig: {
        inputType: "textarea",
        placeholder: "Enter prompt template...",
        column: 2,
        rows: 10
      }
    },
    {
      name: "default_prompt",
      type: "string",
      required: false,
      description: "Default Prompt configuration",
      uiConfig: {
        inputType: "textarea",
        placeholder: "Enter prompt template...",
        column: 2,
        rows: 10
      }
    },
    {
      name: "max_iteration",
      type: "number",
      required: true,
      defaultValue: 1,
      description: "Max Iteration configuration",
      uiConfig: {
        inputType: "number",
        min: 1
      }
    },
    {
      name: "memory_profile",
      type: "string",
      required: false,
      description: "Memory profile for conversation context",
      defaultValue: "FOCUSED",
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
      name: "memory_config",
      type: "object",
      required: false,
      description: "Memory Config configuration (deprecated - use memory_profile or memory_settings)",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "memory_settings",
      type: "object",
      required: false,
      description: "Memory Settings configuration (only used when memory_profile is CUSTOM)",
      nestedFields: [
        {
          name: "view",
          type: "enum",
          required: false,
          description: "Memory view mode",
          defaultValue: MemoryView.ALL_INVOLVED,
          validation: {
            allowedValues: Object.values(MemoryView)
          },
          uiConfig: {
            inputType: "select",
            options: [
              { value: MemoryView.ALL_INVOLVED, label: "All Involved - Messages where person is sender or recipient" },
              { value: MemoryView.SENT_BY_ME, label: "Sent By Me - Messages I sent" },
              { value: MemoryView.SENT_TO_ME, label: "Sent To Me - Messages sent to me" },
              { value: MemoryView.SYSTEM_AND_ME, label: "System and Me - System messages and my interactions" },
              { value: MemoryView.CONVERSATION_PAIRS, label: "Conversation Pairs - Request/response pairs" },
              { value: MemoryView.ALL_MESSAGES, label: "All Messages - All messages in conversation" }
            ]
          }
        },
        {
          name: "max_messages",
          type: "number",
          required: false,
          description: "Maximum number of messages to include",
          uiConfig: {
            inputType: "number",
            min: 1
          }
        },
        {
          name: "preserve_system",
          type: "boolean",
          required: false,
          defaultValue: false,
          description: "Preserve system messages",
          uiConfig: {
            inputType: "checkbox"
          }
        }
      ],
      uiConfig: {
        inputType: "group",
        collapsible: true
      }
    },
    {
      name: "tools",
      type: "string",
      required: false,
      description: "Tools available to the AI agent",
      defaultValue: "none",
      uiConfig: {
        inputType: "select",
        options: [
          { value: "none", label: "None - No tools" },
          { value: "image", label: "Image - Image generation capabilities" },
          { value: "websearch", label: "Web Search - Search the internet" }
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
  }
};