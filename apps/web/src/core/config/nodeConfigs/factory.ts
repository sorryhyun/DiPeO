import { HandleLabel, type NodeType } from '@dipeo/domain-models';
import { createUnifiedConfig, type UnifiedNodeConfig } from '../unifiedConfig';
import type { TypedPanelFieldConfig } from '@/features/diagram-editor/types/panel';
import type {
  StartNodeData,
  ConditionNodeData,
  PersonJobNodeData,
  EndpointNodeData,
  DBNodeData,
  CodeJobNodeData,
  ApiJobNodeData,
  UserResponseNodeData,
  NotionNodeData,
  PersonBatchJobNodeData,
  HookNodeData
} from '@/core/types';

// Map node types to their data types
type NodeDataTypeMap = {
  start: StartNodeData;
  condition: ConditionNodeData;
  job: Record<string, unknown>;
  code_job: CodeJobNodeData;
  api_job: ApiJobNodeData;
  endpoint: EndpointNodeData;
  person_job: PersonJobNodeData;
  person_batch_job: PersonBatchJobNodeData;
  db: DBNodeData;
  user_response: UserResponseNodeData;
  notion: NotionNodeData;
  hook: HookNodeData;
};

// Base interface for node type definitions
interface NodeTypeDefinition<T extends Record<string, unknown> = Record<string, unknown>> {
  label: string;
  icon: string;
  color: string;
  handles?: UnifiedNodeConfig['handles'];
  fields?: UnifiedNodeConfig['fields'];
  defaults?: Record<string, unknown>;
  // Panel configuration
  panelLayout?: 'single' | 'twoColumn';
  panelFieldOrder?: string[];
  panelFieldOverrides?: Partial<Record<keyof T, Partial<TypedPanelFieldConfig<T>>>>;
  panelCustomFields?: Array<TypedPanelFieldConfig<T>>;
}

// Centralized node definitions
export const NODE_DEFINITIONS: {
  [K in NodeType]: NodeTypeDefinition<NodeDataTypeMap[K]>
} = {
  start: {
    label: 'Start',
    icon: '🚀',
    color: 'green',
    handles: {
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
    fields: [
      { name: 'enable_hook', type: 'boolean', label: 'Enable Hook', required: false },
      { name: 'hook_type', type: 'select', label: 'Hook Type', required: false, options: [
        { value: 'webhook', label: 'Webhook' },
        { value: 'file', label: 'File' },
        { value: 'shell', label: 'Shell' }
      ]},
      { name: 'hook_config', type: 'textarea', label: 'Hook Configuration', required: false, placeholder: 'Hook configuration (e.g., URL, file path, or command)' }
    ],
    defaults: { label: 'Start', enable_hook: false, hook_type: 'webhook', hook_config: '' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'enable_hook', 'hook_type', 'hook_config'],
    panelCustomFields: [
      {
        type: 'text',
        name: 'label',
        label: 'Block Label',
        placeholder: 'Start',
        column: 1
      }
    ],
    panelFieldOverrides: {
      enable_hook: { column: 1 },
      hook_type: { 
        column: 1,
        conditional: {
          field: 'enable_hook',
          values: [true]
        }
      },
      hook_config: { 
        column: 2,
        rows: 4,
        conditional: {
          field: 'enable_hook',
          values: [true]
        },
        placeholder: 'Enter webhook URL, file path, or shell command based on hook type',
        validate: (value: unknown, formData: StartNodeData) => {
          if (formData?.enable_hook && (!value || typeof value !== 'string' || value.trim().length === 0)) {
            return { isValid: false, error: 'Hook configuration is required when hook is enabled' };
          }
          return { isValid: true };
        }
      }
    }
  },
  
  condition: {
    label: 'Condition',
    icon: '🔀',
    color: 'orange',
    handles: {
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [
        { id: HandleLabel.CONDITION_TRUE, position: 'right', label: 'true', offset: { x: 0, y: 30 } },
        { id: HandleLabel.CONDITION_FALSE, position: 'right', label: 'false', offset: { x: 0, y: -30 } }
      ]
    },
    fields: [
      { name: 'condition_type', type: 'select', label: 'Condition Type', required: true, options: [
        { value: 'detect_max_iterations', label: 'Detect Max Iterations' },
        { value: 'custom', label: 'Custom Expression' }
      ]},
      { name: 'expression', type: 'textarea', label: 'Expression', required: true, placeholder: 'e.g., {{variable}} == "value"' }
    ],
    defaults: { label: 'Condition', condition_type: 'custom', expression: '' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'condition_type', 'expression'],
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
      condition_type: { column: 1 },
      expression: { 
        column: 2,
        rows: 3,
        placeholder: 'Enter condition expression. Use {{variable_name}} for variables.',
        conditional: {
          field: 'condition_type',
          values: ['custom'],
          operator: 'equals'
        },
        validate: (value: unknown, formData: ConditionNodeData) => {
          // Only validate expression for custom type
          if (formData?.condition_type === 'custom' && (!value || typeof value !== 'string' || value.trim().length === 0)) {
            return { isValid: false, error: 'Expression is required for custom conditions' };
          }
          return { isValid: true };
        }
      }
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
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
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
        validate: (value: unknown) => {
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
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
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
      input: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
    fields: [
      { name: 'output_variable', type: 'string', label: 'Output Variable', required: false, placeholder: 'Variable name to output' },
      { name: 'save_to_file', type: 'boolean', label: 'Save to File', required: false },
      { name: 'file_format', type: 'select', label: 'File Format', required: false, options: [
        { value: 'json', label: 'JSON' },
        { value: 'yaml', label: 'YAML' },
        { value: 'txt', label: 'Text' },
        { value: 'md', label: 'Markdown' }
      ]},
      { name: 'file_name', type: 'string', label: 'File Name', required: false, placeholder: 'output.json' }
    ],
    defaults: { label: 'End', output_variable: '', save_to_file: false, file_format: 'json', file_name: '' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'output_variable', 'save_to_file', 'file_format', 'file_name'],
    panelCustomFields: [
      {
        type: 'text',
        name: 'label',
        label: 'Block Label',
        placeholder: 'End',
        column: 1
      }
    ],
    panelFieldOverrides: {
      output_variable: { column: 1 },
      save_to_file: { column: 2 },
      file_format: { 
        column: 2,
        conditional: {
          field: 'save_to_file',
          values: [true]
        }
      },
      file_name: { 
        column: 2,
        conditional: {
          field: 'save_to_file',
          values: [true]
        },
        validate: (value: unknown, formData: EndpointNodeData) => {
          if (formData?.save_to_file && (!value || typeof value !== 'string' || value.trim().length === 0)) {
            return { isValid: false, error: 'File name is required when saving to file' };
          }
          return { isValid: true };
        }
      }
    }
  },
  
  person_job: {
    label: 'Person Job',
    icon: '🤖',
    color: 'indigo',
    handles: {
      input: [
        { id: HandleLabel.FIRST, position: 'left', label: 'first', offset: { x: 0, y: -60 }, color: '#f59e0b' },
        { id: HandleLabel.DEFAULT, position: 'left', label: 'default', offset: { x: 0, y: 60 }, color: '#2563eb' }
      ],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
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
      tools: '',
      memory_config: {
        forget_mode: 'no_forget'
      }
    },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['labelPersonRow', 'max_iteration', 'tools', 'memory_config.forget_mode', 'default_prompt', 'first_only_prompt'],
    panelFieldOverrides: {
      max_iteration: {
        type: 'maxIteration'
      },
      default_prompt: {
        rows: 6,
        placeholder: 'Enter default prompt. Use {{variable_name}} for variables.',
        column: 2,
        showPromptFileButton: true,
        validate: (value: unknown) => {
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
        validate: (value: unknown) => {
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
      },
      {
        type: 'select',
        name: 'memory_config.forget_mode',
        label: 'Forget Mode',
        column: 1,
        options: [
          { value: 'no_forget', label: 'No Forget (Keep all history)' },
          { value: 'on_every_turn', label: 'On Every Turn' },
          { value: 'upon_request', label: 'Upon Request' }
        ]
      }
    ]
  },
  
  person_batch_job: {
    label: 'Person Batch Job',
    icon: '📋',
    color: 'purple',
    handles: {
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
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
        validate: (value: unknown) => {
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
      input: [{ id: HandleLabel.DEFAULT, position: 'bottom', offset: { x: -30, y: 0 } }],
      output: [{ id: HandleLabel.DEFAULT, position: 'bottom', offset: { x: 30, y: 0 } }]
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
        validate: (value: unknown, formData: DBNodeData) => {
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
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
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
        validate: (value: unknown) => {
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
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
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
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
    fields: [
      { name: 'hook_type', type: 'select', label: 'Hook Type', required: true, options: [
        { value: 'webhook', label: 'Webhook' },
        { value: 'file', label: 'File' },
        { value: 'shell', label: 'Shell' }
      ]},
      { name: 'command', type: 'string', label: 'Command', required: true, placeholder: 'Command to execute' }
    ],
    defaults: { label: 'Hook', hook_type: 'webhook', command: '' }
  }
};

// Factory function to create node configs
export function createNodeConfigs(definitions: typeof NODE_DEFINITIONS = NODE_DEFINITIONS): {
  [K in NodeType]: UnifiedNodeConfig<NodeDataTypeMap[K]>
} {
  const configs: Record<string, UnifiedNodeConfig<any>> = {};
  
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
    } as any);
  }
  
  return configs as {
    [K in NodeType]: UnifiedNodeConfig<NodeDataTypeMap[K]>
  };
}

// Export the node configs using the factory
export const nodeConfigs = createNodeConfigs();