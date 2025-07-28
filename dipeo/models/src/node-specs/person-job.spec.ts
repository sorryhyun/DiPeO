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
      name: "memory_config",
      type: "object",
      required: false,
      description: "Memory Config configuration (deprecated - use memory_settings)",
      uiConfig: {
        inputType: "code",
        collapsible: true
      }
    },
    {
      name: "memory_settings",
      type: "object",
      required: false,
      description: "Memory Settings configuration",
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
      type: "array",
      required: false,
      description: "Tools configuration",
      validation: {
        itemType: "object"
      },
      uiConfig: {
        inputType: "code",
        collapsible: true
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