// Unified node configuration system - single source of truth
import type { Node, NodeType, PanelConfig } from '@/types';

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

// Panel configurations for advanced property panels
export const PANEL_CONFIGS: Record<NodeType | 'arrow' | 'person', PanelConfig<Record<string, any>>> = {
  start: {
    layout: 'single',
    fields: [
      {
        type: 'text',
        name: 'label',
        label: 'Block Label',
        placeholder: 'Start'
      }
    ]
  },

  condition: {
    layout: 'single',
    fields: [
      {
        type: 'row',
        className: 'grid grid-cols-2 gap-2',
        fields: [
          {
            type: 'text',
            name: 'label',
            label: 'Block Label',
            placeholder: 'Condition'
          },
          {
            type: 'select',
            name: 'conditionType',
            label: 'Condition Type',
            options: [
              { value: 'expression', label: 'Expression' },
              { value: 'detect_max_iterations', label: 'Max Iterations' }
            ]
          }
        ]
      },
      {
        type: 'textarea',
        name: 'expression',
        label: 'Python Expression',
        rows: 3,
        placeholder: 'e.g., x > 10 and y == \'yes\'',
        conditional: {
          field: 'conditionType',
          values: ['expression'],
          operator: 'equals'
        }
      }
    ]
  },

  job: {
    layout: 'twoColumn',
    leftColumn: [
      {
        type: 'row',
        fields: [
          {
            type: 'text',
            name: 'label',
            label: 'Label',
            placeholder: 'Job',
            className: 'flex-1'
          },
          {
            type: 'select',
            name: 'subType',
            label: 'Type',
            options: [
              { value: 'code', label: 'Code Execution' },
              { value: 'api_tool', label: 'API Tool' },
              { value: 'diagram_link', label: 'Diagram Link' }
            ],
            className: 'flex-1'
          }
        ]
      },
      {
        type: 'row',
        fields: [
          {
            type: 'maxIteration',
            name: 'maxIteration',
            label: 'Max Iter',
            className: 'flex-1'
          }
        ]
      }
    ],
    rightColumn: [
      {
        type: 'textarea',
        name: 'sourceDetails',
        label: 'Details',
        rows: 6,
        placeholder: 'Enter job details...'
      },
      {
        type: 'textarea',
        name: 'firstOnlyPrompt',
        label: 'First-Only Prompt',
        rows: 4,
        placeholder: 'Prompt to use only on first execution.'
      }
    ]
  },

  endpoint: {
    layout: 'twoColumn',
    leftColumn: [
      {
        type: 'text',
        name: 'label',
        label: 'Block Label',
        placeholder: 'End'
      },
      {
        type: 'checkbox',
        name: 'saveToFile',
        label: 'Save output to file'
      },
      {
        type: 'row',
        fields: [
          {
            type: 'text',
            name: 'filePath',
            label: 'File Path',
            placeholder: 'results/output.txt',
            conditional: {
              field: 'saveToFile',
              values: [true]
            },
            className: 'flex-1'
          },
          {
            type: 'select',
            name: 'fileFormat',
            label: 'File Format',
            options: [
              { value: 'text', label: 'Plain Text' },
              { value: 'json', label: 'JSON' },
              { value: 'csv', label: 'CSV' }
            ],
            conditional: {
              field: 'saveToFile',
              values: [true]
            },
            className: 'flex-1'
          }
        ]
      }
    ],
    rightColumn: []
  },

  person_job: {
    layout: 'twoColumn',
    leftColumn: [
      {
        type: 'labelPersonRow',
        labelPlaceholder: 'Person Job'
      },
      {
        type: 'row',
        fields: [
          {
            type: 'select',
            name: 'contextCleaningRule',
            label: 'Forget',
            options: [
              { value: 'upon_request', label: 'Upon This Request' },
              { value: 'no_forget', label: 'Do Not Forget' },
              { value: 'on_every_turn', label: 'On Every Turn' }
            ],
            className: 'flex-1'
          },
          {
            type: 'maxIteration',
            name: 'maxIteration',
            className: 'flex-1'
          }
        ]
      },
      {
        type: 'checkbox',
        name: 'interactive',
        label: 'Interactive Mode - Wait for user input before LLM call'
      }
    ],
    rightColumn: [
      {
        type: 'variableTextArea',
        name: 'defaultPrompt',
        label: 'Default Prompt',
        rows: 6,
        placeholder: 'Enter default prompt. Use {{variable_name}} for variables.'
      },
      {
        type: 'variableTextArea',
        name: 'firstOnlyPrompt',
        label: 'First-Only Prompt',
        rows: 4,
        placeholder: 'Prompt to use only on first execution.'
      }
    ]
  },

  person_batch_job: {
    layout: 'twoColumn',
    leftColumn: [
      {
        type: 'labelPersonRow',
        labelPlaceholder: 'Person Batch Job'
      },
      {
        type: 'row',
        fields: [
          {
            type: 'text',
            name: 'batchSize',
            label: 'Batch Size',
            placeholder: '10',
            className: 'w-24'
          },
          {
            type: 'maxIteration',
            name: 'maxIteration'
          }
        ]
      },
      {
        type: 'checkbox',
        name: 'parallelProcessing',
        label: 'Enable Parallel Processing'
      },
      {
        type: 'row',
        fields: [
          {
            type: 'select',
            name: 'aggregationMethod',
            label: 'Aggregation',
            options: [
              { value: 'concatenate', label: 'Concatenate' },
              { value: 'summarize', label: 'Summarize' },
              { value: 'custom', label: 'Custom' }
            ],
            className: 'flex-1'
          }
        ]
      }
    ],
    rightColumn: [
      {
        type: 'variableTextArea',
        name: 'batchPrompt',
        label: 'Batch Prompt',
        rows: 6,
        placeholder: 'Enter batch processing prompt. Use {{variable_name}} for variables.'
      },
      {
        type: 'variableTextArea',
        name: 'customAggregationPrompt',
        label: 'Custom Aggregation Prompt',
        rows: 4,
        placeholder: 'Enter custom aggregation prompt to process batch results.',
        conditional: {
          field: 'aggregationMethod',
          values: ['custom']
        }
      }
    ]
  },

  db: {
    layout: 'twoColumn',
    leftColumn: [
      {
        type: 'row',
        fields: [
          {
            type: 'text',
            name: 'label',
            label: 'Label',
            placeholder: 'Database',
            className: 'flex-1'
          },
          {
            type: 'select',
            name: 'subType',
            label: 'Source Type',
            options: [
              { value: 'fixed_prompt', label: 'Fixed Prompt' },
              { value: 'file', label: 'File' }
            ],
            className: 'flex-1'
          }
        ]
      }
    ],
    rightColumn: [
      {
        type: 'textarea',
        name: 'sourceDetails',
        label: 'Source Details',
        rows: 5,
        placeholder: 'For Fixed Prompt: Enter your text content\nFor File: Enter the file path (e.g., data/input.txt)'
      }
    ]
  },

  user_response: {
    layout: 'single',
    fields: [
      {
        type: 'text',
        name: 'label',
        label: 'Name',
        placeholder: 'User Response'
      },
      {
        type: 'textarea',
        name: 'prompt',
        label: 'Prompt Message',
        placeholder: 'Enter the message to show to the user...',
        rows: 3
      },
      {
        type: 'text',
        name: 'timeout',
        label: 'Timeout (seconds)',
        placeholder: '10'
      }
    ]
  },

  notion: {
    layout: 'single',
    fields: [
      {
        name: 'label',
        label: 'Label',
        type: 'text',
        placeholder: 'Notion'
      },
      {
        name: 'operation',
        label: 'Operation',
        type: 'select',
        options: [
          { value: 'read_page', label: 'Read Page' },
          { value: 'list_blocks', label: 'List Blocks' },
          { value: 'append_blocks', label: 'Append Blocks' },
          { value: 'update_block', label: 'Update Block' },
          { value: 'query_database', label: 'Query Database' },
          { value: 'create_page', label: 'Create Page' },
          { value: 'extract_text', label: 'Extract Text from Blocks' }
        ]
      },
      {
        name: 'apiKeyId',
        label: 'API Key',
        type: 'select',
        options: []
      },
      {
        name: 'pageId',
        label: 'Page ID',
        type: 'text',
        placeholder: 'Enter Notion page ID (e.g., 202c8edd335e8059af75fe79d0451885)',
        conditional: {
          field: 'operation',
          values: ['read_page', 'list_blocks', 'append_blocks']
        }
      },
      {
        name: 'blockId',
        label: 'Block ID',
        type: 'text',
        placeholder: 'Enter block ID',
        conditional: {
          field: 'operation',
          values: ['update_block']
        }
      },
      {
        name: 'databaseId',
        label: 'Database ID',
        type: 'text',
        placeholder: 'Enter database ID',
        conditional: {
          field: 'operation',
          values: ['query_database']
        }
      }
    ]
  },

  arrow: {
    layout: 'twoColumn',
    leftColumn: [
      {
        type: 'text',
        name: 'label',
        label: 'Arrow Label',
        placeholder: 'e.g., user_query',
        conditional: {
          field: '_sourceNodeType',
          values: ['condition'],
          operator: 'notEquals'
        }
      },
      {
        type: 'text',
        name: 'label',
        label: 'Arrow Label',
        placeholder: 'e.g., true, false, or custom label',
        conditional: {
          field: '_sourceNodeType',
          values: ['condition'],
          operator: 'equals'
        }
      },
      {
        type: 'text',
        name: 'objectKeyPath',
        label: 'Object Key Path',
        placeholder: 'e.g., user.name or data.items[0].value',
        conditional: {
          field: 'contentType',
          values: ['variable_in_object']
        }
      }
    ],
    rightColumn: [
      {
        type: 'select',
        name: 'contentType',
        label: 'Content Type',
        options: [
          { value: 'raw_text', label: 'Raw Text' },
          { value: 'variable_in_object', label: 'Variable in Object' },
          { value: 'conversation_state', label: 'Conversation State' }
        ],
        conditional: {
          field: '_sourceNodeType',
          values: ['condition', 'start'],
          operator: 'notEquals'
        }
      },
      {
        type: 'select',
        name: 'contentType',
        label: 'Content Type (Inherited from condition input)',
        options: [
          { value: 'raw_text', label: 'Raw Text' },
          { value: 'variable_in_object', label: 'Variable in Object' },
          { value: 'conversation_state', label: 'Conversation State' },
          { value: 'generic', label: 'Generic' }
        ],
        disabled: true,
        conditional: {
          field: '_sourceNodeType',
          values: ['condition'],
          operator: 'equals'
        }
      },
      {
        type: 'select',
        name: 'contentType',
        label: 'Content Type',
        options: [
          { value: 'empty', label: 'Empty (Fixed)' }
        ],
        disabled: true,
        conditional: {
          field: '_sourceNodeType',
          values: ['start'],
          operator: 'equals'
        }
      }
    ]
  },

  person: {
    layout: 'twoColumn',
    leftColumn: [
      {
        type: 'text',
        name: 'label',
        label: 'Person Name',
        placeholder: 'Person Name'
      },
      {
        type: 'row',
        fields: [
          {
            type: 'select',
            name: 'service',
            label: 'Service',
            options: [
              { value: 'openai', label: 'OpenAI' },
              { value: 'claude', label: 'Claude' },
              { value: 'gemini', label: 'Gemini' },
              { value: 'grok', label: 'Grok' },
              { value: 'custom', label: 'Custom' }
            ],
            className: 'flex-1'
          },
          {
            type: 'select',
            name: 'apiKeyId',
            label: 'API Key',
            options: [], // Dynamic options
            placeholder: 'Select API Key',
            className: 'flex-1'
          }
        ]
      },
      {
        type: 'select',
        name: 'modelName',
        label: 'Model',
        options: [], // Dynamic options based on service
        placeholder: 'Select Model'
      }
    ],
    rightColumn: [
      {
        type: 'textarea',
        name: 'systemPrompt',
        label: 'System Prompt',
        placeholder: 'Enter system prompt',
        rows: 4
      }
    ]
  }
};

// Simple node configurations for basic rendering
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
      { name: 'maxIteration', type: 'number', label: 'Max Iterations', required: true, min: 1, max: 100 },
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
    defaults: { personId: '', maxIteration: 1, firstOnlyPrompt: '', defaultPrompt: '', contextCleaningRule: 'none' }
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

// Get panel configuration for advanced property panels
export function getPanelConfig(type: NodeType | 'arrow' | 'person') {
  return PANEL_CONFIGS[type] || null;
}