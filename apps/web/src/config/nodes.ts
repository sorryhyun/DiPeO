// Simplified node configuration system - single source of truth
import type { Node } from '../common/types/core';

export type NodeType = Node['type'];

interface FieldConfig {
  name: string;
  type: 'string' | 'number' | 'select' | 'textarea' | 'person' | 'boolean';
  label: string;
  required?: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
  min?: number;
  max?: number;
  multiline?: boolean;
}

interface HandleConfig {
  id: string;
  position: 'top' | 'right' | 'bottom' | 'left';
  label?: string;
  offset?: { x: number; y: number };
}

interface NodeConfigItem {
  label: string;
  icon: string;
  color: string;
  handles: {
    input?: HandleConfig[];
    output?: HandleConfig[];
  };
  fields: FieldConfig[];
  defaults: Record<string, any>;
}

export const NODE_CONFIGS: Record<NodeType, NodeConfigItem> = {
  start: {
    label: 'Start',
    icon: '🚀',
    color: 'green',
    handles: {
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { name: 'output', type: 'textarea', label: 'Output Data', required: true, placeholder: 'Enter static data to output' }
    ],
    defaults: { output: '' }
  },

  condition: {
    label: 'Condition',
    icon: '🔀',
    color: 'purple',
    handles: {
      input: [{ id: 'default', position: 'left' }],
      output: [
        { id: 'true', position: 'right', label: 'True', offset: { x: 0, y: -15 } },
        { id: 'false', position: 'right', label: 'False', offset: { x: 0, y: 15 } }
      ]
    },
    fields: [
      { 
        name: 'conditionType', 
        type: 'select', 
        label: 'Condition Type', 
        required: true,
        options: [
          { value: 'simple', label: 'Simple Condition' },
          { value: 'complex', label: 'Complex Condition' },
          { value: 'detect_max_iterations', label: 'Detect Max Iterations' }
        ]
      },
      { name: 'condition', type: 'string', label: 'Condition', required: true, placeholder: 'e.g., {{value}} > 10' }
    ],
    defaults: { conditionType: 'simple', condition: '' }
  },

  job: {
    label: 'Job',
    icon: '⚙️',
    color: 'blue',
    handles: {
      input: [{ id: 'default', position: 'left' }],
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { 
        name: 'subType', 
        type: 'select', 
        label: 'Language', 
        required: true,
        options: [
          { value: 'python', label: 'Python' },
          { value: 'javascript', label: 'JavaScript' },
          { value: 'bash', label: 'Bash' }
        ]
      },
      { name: 'code', type: 'textarea', label: 'Code', required: true, placeholder: 'Enter your code here...' }
    ],
    defaults: { subType: 'python', code: '' }
  },

  endpoint: {
    label: 'Endpoint',
    icon: '🎯',
    color: 'red',
    handles: {
      input: [{ id: 'default', position: 'left' }]
    },
    fields: [
      { 
        name: 'action', 
        type: 'select', 
        label: 'Action', 
        required: true,
        options: [
          { value: 'save', label: 'Save to File' },
          { value: 'output', label: 'Output Result' }
        ]
      },
      { name: 'filename', type: 'string', label: 'Filename', placeholder: 'output.txt' }
    ],
    defaults: { action: 'output', filename: '' }
  },

  person_job: {
    label: 'Person Job',
    icon: '🤖',
    color: 'indigo',
    handles: {
      input: [
        { id: 'first', position: 'left', label: 'First', offset: { x: 0, y: -15 } },
        { id: 'default', position: 'left', label: 'Default', offset: { x: 0, y: 15 } }
      ],
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { name: 'personId', type: 'person', label: 'Person', required: true, placeholder: 'Select person...' },
      { name: 'iterationCount', type: 'number', label: 'Max Iterations', required: true, min: 1, max: 100 },
      { name: 'firstOnlyPrompt', type: 'textarea', label: 'First Iteration Prompt', required: true, placeholder: 'Prompt for first iteration (uses "first" input)' },
      { name: 'defaultPrompt', type: 'textarea', label: 'Default Prompt', required: true, placeholder: 'Prompt for subsequent iterations (uses "default" input)' },
      { 
        name: 'contextCleaningRule', 
        type: 'select', 
        label: 'Context Cleaning', 
        required: true,
        options: [
          { value: 'none', label: 'No Cleaning' },
          { value: 'trim', label: 'Trim Old Messages' },
          { value: 'summarize', label: 'Summarize Context' }
        ]
      }
    ],
    defaults: { personId: '', iterationCount: 1, firstOnlyPrompt: '', defaultPrompt: '', contextCleaningRule: 'none' }
  },

  person_batch_job: {
    label: 'Person Batch Job',
    icon: '🤖🔁',
    color: 'indigo',
    handles: {
      input: [{ id: 'default', position: 'left' }],
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { name: 'personId', type: 'person', label: 'Person', required: true, placeholder: 'Select person...' },
      { name: 'prompt', type: 'textarea', label: 'Prompt Template', required: true, placeholder: 'Process: {{item}}' },
      { name: 'batchSize', type: 'number', label: 'Batch Size', required: true, min: 1, max: 100 }
    ],
    defaults: { personId: '', prompt: '', batchSize: 10 }
  },

  db: {
    label: 'Database',
    icon: '💾',
    color: 'yellow',
    handles: {
      input: [{ id: 'default', position: 'top' }],
      output: [{ id: 'default', position: 'bottom' }]
    },
    fields: [
      { 
        name: 'operation', 
        type: 'select', 
        label: 'Operation', 
        required: true,
        options: [
          { value: 'read', label: 'Read File' },
          { value: 'write', label: 'Write File' },
          { value: 'query', label: 'Query Database' }
        ]
      },
      { name: 'path', type: 'string', label: 'File Path', required: true, placeholder: 'data/file.json' },
      { 
        name: 'format', 
        type: 'select', 
        label: 'Format', 
        required: true,
        options: [
          { value: 'json', label: 'JSON' },
          { value: 'csv', label: 'CSV' },
          { value: 'text', label: 'Text' }
        ]
      }
    ],
    defaults: { operation: 'read', path: '', format: 'json' }
  },

  user_response: {
    label: 'User Response',
    icon: '❓',
    color: 'indigo',
    handles: {
      input: [{ id: 'default', position: 'left' }],
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { name: 'promptMessage', type: 'textarea', label: 'Prompt Message', required: true, placeholder: 'Enter the message to display to the user...' },
      { name: 'timeoutSeconds', type: 'number', label: 'Timeout (seconds)', min: 1, max: 60, placeholder: '10' }
    ],
    defaults: { promptMessage: '', timeoutSeconds: 10 }
  },

  notion: {
    label: 'Notion',
    icon: '📄',
    color: 'gray',
    handles: {
      input: [{ id: 'default', position: 'left' }],
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { 
        name: 'operation', 
        type: 'select', 
        label: 'Operation', 
        required: true,
        options: [
          { value: 'read_page', label: 'Read Page' },
          { value: 'list_blocks', label: 'List Blocks' },
          { value: 'append_blocks', label: 'Append Blocks' },
          { value: 'update_block', label: 'Update Block' },
          { value: 'query_database', label: 'Query Database' },
          { value: 'create_page', label: 'Create Page' },
          { value: 'extract_text', label: 'Extract Text' }
        ]
      },
      { name: 'apiKeyId', type: 'string', label: 'API Key', required: true, placeholder: 'Select API key...' },
      { name: 'pageId', type: 'string', label: 'Page ID', placeholder: 'Notion page ID' },
      { name: 'blockId', type: 'string', label: 'Block ID', placeholder: 'Notion block ID' },
      { name: 'databaseId', type: 'string', label: 'Database ID', placeholder: 'Notion database ID' }
    ],
    defaults: { operation: 'read_page', apiKeyId: '', pageId: '', blockId: '', databaseId: '' }
  }
} as const;

// Helper function
export function getNodeConfig(type: NodeType) {
  return NODE_CONFIGS[type] || NODE_CONFIGS.start;
}

// Simple validation
export function validateNodeData(type: NodeType, data: Record<string, any>) {
  const config = getNodeConfig(type);
  const errors: string[] = [];
  
  config.fields.forEach(field => {
    if (field.required && !data[field.name]) {
      errors.push(`${field.label} is required`);
    }
  });
  
  return { valid: errors.length === 0, errors };
}

// Get default data for a node type
export function getNodeDefaults(type: NodeType) {
  return { ...getNodeConfig(type).defaults };
}

// Get color class names for a node
export function getNodeColorClasses(type: NodeType) {
  const color = getNodeConfig(type).color;
  return {
    border: `border-${color}-500`,
    bg: `bg-${color}-50`,
    hover: `hover:bg-${color}-100`
  };
}