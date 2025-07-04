import type { NodeType } from '@dipeo/domain-models';
import { createUnifiedConfig, type UnifiedNodeConfig } from '../unifiedConfig';

// Base interface for node type definitions
interface NodeTypeDefinition {
  label: string;
  icon: string;
  color: string;
  handles?: UnifiedNodeConfig['handles'];
  fields?: UnifiedNodeConfig['fields'];
  defaults?: Record<string, unknown>;
  // Panel configuration
  panelLayout?: 'single' | 'twoColumn';
  panelFieldOrder?: string[];
  panelFieldOverrides?: Record<string, any>;
  panelCustomFields?: any[];
}

// Centralized node definitions
export const NODE_DEFINITIONS: Record<NodeType, NodeTypeDefinition> = {
  start: {
    label: 'Start',
    icon: '🚀',
    color: 'green',
    handles: {
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [],
    defaults: { label: 'Start' },
    panelCustomFields: [
      {
        type: 'text',
        name: 'label',
        label: 'Block Label',
        placeholder: 'Start'
      }
    ]
  },
  
  condition: {
    label: 'Condition',
    icon: '🔀',
    color: 'orange',
    handles: {
      input: [{ id: 'default', position: 'left' }],
      output: [
        { id: 'true', position: 'right', label: 'True', offset: { x: 0, y: 30 } },
        { id: 'false', position: 'right', label: 'False', offset: { x: 0, y: -30 } }
      ]
    },
    fields: [
      { name: 'input_variable', type: 'string', label: 'Input Variable', required: true, placeholder: 'Variable to check' },
      { name: 'target_value', type: 'string', label: 'Target Value', required: true, placeholder: 'Value to match' }
    ],
    defaults: { label: 'Condition', input_variable: '', target_value: '' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'input_variable', 'target_value'],
    panelCustomFields: [
      {
        type: 'text',
        name: 'label',
        label: 'Block Label',
        placeholder: 'Condition',
        column: 1
      }
    ],
    panelFieldOverrides: {
      input_variable: { column: 1 },
      target_value: { column: 2 }
    }
  },
  
  job: {
    label: 'Job (Deprecated)',
    icon: '⚙️',
    color: 'gray',
    handles: {},
    fields: [],
    defaults: {}
  },
  
  code_job: {
    label: 'Code Job',
    icon: '💻',
    color: 'purple',
    handles: {
      input: [{ id: 'default', position: 'left' }],
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { name: 'language', type: 'select', label: 'Language', required: true, options: [
        { value: 'python', label: 'Python' },
        { value: 'javascript', label: 'JavaScript' },
        { value: 'bash', label: 'Bash' }
      ]},
      { name: 'code', type: 'textarea', label: 'Code', required: true, placeholder: 'Enter your code here' }
    ],
    defaults: { label: 'Code Job', language: 'python', code: '' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'language', 'code'],
    panelCustomFields: [
      {
        type: 'text',
        name: 'label',
        label: 'Block Label',
        placeholder: 'Code Job',
        column: 1
      }
    ],
    panelFieldOverrides: {
      language: { column: 1 },
      code: { 
        rows: 8,
        column: 2,
        validate: (value: any) => {
          if (!value || typeof value !== 'string' || value.trim().length === 0) {
            return { isValid: false, error: 'Code is required' };
          }
          return { isValid: true };
        }
      }
    }
  },
  
  api_job: {
    label: 'API Job',
    icon: '🌐',
    color: 'teal',
    handles: {
      input: [{ id: 'default', position: 'left' }],
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { name: 'url', type: 'string', label: 'URL', required: true, placeholder: 'https://api.example.com/endpoint' },
      { name: 'method', type: 'select', label: 'Method', required: true, options: [
        { value: 'GET', label: 'GET' },
        { value: 'POST', label: 'POST' },
        { value: 'PUT', label: 'PUT' },
        { value: 'DELETE', label: 'DELETE' }
      ]},
      { name: 'headers', type: 'textarea', label: 'Headers', required: false, placeholder: 'JSON format headers' },
      { name: 'body', type: 'textarea', label: 'Body', required: false, placeholder: 'Request body' }
    ],
    defaults: { label: 'API Job', url: '', method: 'GET', headers: '', body: '' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'url', 'method', 'headers', 'body'],
    panelCustomFields: [
      {
        type: 'text',
        name: 'label',
        label: 'Block Label',
        placeholder: 'API Job',
        column: 1
      }
    ],
    panelFieldOverrides: {
      url: { column: 1 },
      method: { column: 1 },
      headers: { column: 2, rows: 4 },
      body: { column: 2, rows: 6 }
    }
  },
  
  endpoint: {
    label: 'Endpoint',
    icon: '🎯',
    color: 'red',
    handles: {
      input: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { name: 'output_variable', type: 'string', label: 'Output Variable', required: false, placeholder: 'Variable name to output' }
    ],
    defaults: { label: 'End', output_variable: '' },
    panelCustomFields: [
      {
        type: 'text',
        name: 'label',
        label: 'Block Label',
        placeholder: 'End'
      }
    ]
  },
  
  person_job: {
    label: 'Person Job',
    icon: '🤖',
    color: 'indigo',
    handles: {
      input: [
        { id: 'first', position: 'left', label: 'first', offset: { x: 0, y: -60 }, color: '#f59e0b' },
        { id: 'default', position: 'left', label: 'default', offset: { x: 0, y: 60 }, color: '#2563eb' }
      ],
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { name: 'max_iteration', type: 'number', label: 'Max Iterations', required: true, min: 1, max: 100 },
      { name: 'first_only_prompt', type: 'textarea', label: 'First Iteration Prompt', required: true, placeholder: 'Prompt for first iteration (uses "first" input)' },
      { name: 'default_prompt', type: 'textarea', label: 'Default Prompt', required: true, placeholder: 'Prompt for subsequent iterations (uses "default" input)' },
      { name: 'tools', type: 'string', label: 'Tools', required: false, placeholder: 'Enter tool names separated by commas (e.g., web_search, image_generation)' }
    ],
    defaults: { 
      person: '', 
      max_iteration: 1, 
      first_only_prompt: '', 
      default_prompt: '',
      tools: ''
    },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['labelPersonRow', 'max_iteration', 'tools', 'default_prompt', 'first_only_prompt'],
    panelFieldOverrides: {
      max_iteration: {
        type: 'maxIteration'
      },
      default_prompt: {
        rows: 6,
        placeholder: 'Enter default prompt. Use {{variable_name}} for variables.',
        column: 2,
        showPromptFileButton: true,
        validate: (value: any) => {
          if (!value && typeof value !== 'string') {
            return { isValid: false, error: 'Default prompt is recommended' };
          }
          return { isValid: true };
        }
      },
      first_only_prompt: {
        label: 'First-Only Prompt',
        rows: 4,
        placeholder: 'Prompt to use only on first execution.',
        column: 2,
        showPromptFileButton: true,
        validate: (value: any) => {
          if (!value || typeof value !== 'string' || value.trim().length === 0) {
            return { isValid: false, error: 'First-only prompt is required' };
          }
          return { isValid: true };
        }
      }
    },
    panelCustomFields: [
      {
        type: 'labelPersonRow',
        labelPlaceholder: 'Person Job'
      }
    ]
  },
  
  person_batch_job: {
    label: 'Person Batch Job',
    icon: '📋',
    color: 'purple',
    handles: {
      input: [{ id: 'default', position: 'left' }],
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { name: 'batch_key', type: 'string', label: 'Batch Key', required: true, placeholder: 'Variable containing array to iterate over' },
      { name: 'prompt', type: 'textarea', label: 'Prompt', required: true, placeholder: 'Prompt to execute for each item. Use {{item}} for current item.' }
    ],
    defaults: { 
      person: '', 
      batch_key: '', 
      prompt: ''
    },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['labelPersonRow', 'batch_key', 'prompt'],
    panelFieldOverrides: {
      batch_key: { column: 1 },
      prompt: {
        rows: 8,
        placeholder: 'Enter prompt. Use {{item}} for current batch item, {{variable_name}} for other variables.',
        column: 2,
        showPromptFileButton: true,
        validate: (value: any) => {
          if (!value || typeof value !== 'string' || value.trim().length === 0) {
            return { isValid: false, error: 'Prompt is required' };
          }
          return { isValid: true };
        }
      }
    },
    panelCustomFields: [
      {
        type: 'labelPersonRow',
        labelPlaceholder: 'Person Batch Job'
      }
    ]
  },
  
  db: {
    label: 'Database',
    icon: '💾',
    color: 'yellow',
    handles: {
      input: [{ id: 'default', position: 'bottom', offset: { x: -30, y: 0 } }],
      output: [{ id: 'default', position: 'bottom', offset: { x: 30, y: 0 } }]
    },
    fields: [],
    defaults: { label: '', sub_type: 'fixed_prompt', source_details: '', operation: 'read' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'sub_type', 'operation', 'source_details'],
    panelCustomFields: [
      {
        type: 'text',
        name: 'label',
        label: 'Block Label',
        placeholder: 'Database',
        column: 1
      },
      {
        type: 'select',
        name: 'sub_type',
        label: 'Source Type',
        options: [
          { value: 'fixed_prompt', label: 'Fixed Prompt' },
          { value: 'file', label: 'File' }
        ],
        column: 1
      },
      {
        type: 'select',
        name: 'operation',
        label: 'Operation',
        options: [
          { value: 'prompt', label: 'Prompt' },
          { value: 'read', label: 'Read' },
          { value: 'write', label: 'Write' },
          { value: 'update', label: 'Update' },
          { value: 'delete', label: 'Delete' }
        ],
        column: 1
      },
      {
        type: 'variableTextArea',
        name: 'source_details',
        label: 'Source Details',
        rows: 6,
        placeholder: 'Enter content or file path...',
        column: 2,
        showPromptFileButton: true,
        validate: (value: any, formData: any) => {
          if (!value || typeof value !== 'string' || value.trim().length === 0) {
            return { isValid: false, error: 'Source details are required' };
          }
          if (formData?.sub_type === 'file' && !value.includes('.')) {
            return { isValid: false, error: 'Please provide a valid file path with extension' };
          }
          return { isValid: true };
        }
      }
    ]
  },
  
  user_response: {
    label: 'User Response',
    icon: '👤',
    color: 'cyan',
    handles: {
      input: [{ id: 'default', position: 'left' }],
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { name: 'prompt', type: 'textarea', label: 'Prompt', required: true, placeholder: 'Question to ask the user' }
    ],
    defaults: { label: 'User Response', prompt: '' },
    panelCustomFields: [
      {
        type: 'text',
        name: 'label',
        label: 'Block Label',
        placeholder: 'User Response'
      }
    ],
    panelFieldOverrides: {
      prompt: {
        rows: 4,
        placeholder: 'Enter the question to ask the user. Use {{variable_name}} for variables.',
        showPromptFileButton: true,
        validate: (value: any) => {
          if (!value || typeof value !== 'string' || value.trim().length === 0) {
            return { isValid: false, error: 'Prompt is required' };
          }
          return { isValid: true };
        }
      }
    }
  },
  
  notion: {
    label: 'Notion',
    icon: '📝',
    color: 'gray',
    handles: {
      input: [{ id: 'default', position: 'left' }],
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { name: 'page_id', type: 'string', label: 'Page ID', required: true, placeholder: 'Notion page ID' },
      { name: 'operation', type: 'select', label: 'Operation', required: true, options: [
        { value: 'read', label: 'Read' },
        { value: 'write', label: 'Write' }
      ]}
    ],
    defaults: { label: 'Notion', page_id: '', operation: 'read' }
  },
  
  hook: {
    label: 'Hook',
    icon: '🪝',
    color: 'pink',
    handles: {
      input: [{ id: 'default', position: 'left' }],
      output: [{ id: 'default', position: 'right' }]
    },
    fields: [
      { name: 'hook_type', type: 'select', label: 'Hook Type', required: true, options: [
        { value: 'before', label: 'Before' },
        { value: 'after', label: 'After' }
      ]},
      { name: 'command', type: 'string', label: 'Command', required: true, placeholder: 'Command to execute' }
    ],
    defaults: { label: 'Hook', hook_type: 'before', command: '' }
  }
};

// Factory function to create node configs
export function createNodeConfigs(definitions: typeof NODE_DEFINITIONS = NODE_DEFINITIONS): Record<NodeType, UnifiedNodeConfig<Record<string, unknown>>> {
  const configs: Record<string, UnifiedNodeConfig<Record<string, unknown>>> = {};
  
  for (const [nodeType, definition] of Object.entries(definitions)) {
    configs[nodeType] = createUnifiedConfig({
      label: definition.label,
      icon: definition.icon,
      color: definition.color,
      handles: definition.handles || {},
      fields: definition.fields || [],
      defaults: definition.defaults || {},
      panelLayout: definition.panelLayout,
      panelFieldOrder: definition.panelFieldOrder,
      panelFieldOverrides: definition.panelFieldOverrides,
      panelCustomFields: definition.panelCustomFields
    });
  }
  
  return configs as Record<NodeType, UnifiedNodeConfig<Record<string, unknown>>>;
}

// Export the node configs using the factory
export const nodeConfigs = createNodeConfigs();