import type { NodeType } from './node';
import React from 'react';
import { PropertyFieldConfig, FieldConfig } from './fieldConfig';

// Re-export FieldConfig for backward compatibility
export type { FieldConfig };


export interface NodeConfig {
  // Visual properties
  label: string;
  description: string;
  emoji: string;
  borderColor: string;
  width: number;
  className?: string;
  category?: 'flow' | 'data' | 'llm' | 'control';
  reactFlowType: string;
  blockType: string;
  
  // Handle configuration
  handles: {
    sources: Array<{
      id: string;
      position: 'top' | 'right' | 'bottom' | 'left';
      offset?: { x: number; y: number };
      label?: string;
      color?: string;
      style?: React.CSSProperties;
    }>;
    targets: Array<{
      id: string;
      position: 'top' | 'right' | 'bottom' | 'left';
      offset?: { x: number; y: number };
      label?: string;
      color?: string;
      style?: React.CSSProperties;
    }>;
  };
  
  // Property fields
  propertyFields: PropertyFieldConfig[];
  
  // Default values for the node
  defaultData: Record<string, unknown>;
  
  // Validation rules
  validation?: {
    requiredFields: string[];
    customValidation?: (data: unknown) => { valid: boolean; errors?: string[] };
  };
  
  // Node-specific behavior
  behavior?: {
    allowMultiple?: boolean;
    isRequired?: boolean;
    customRenderer?: (data: unknown) => React.ReactNode;
    verticalHandles?: boolean;
  };
}

/**
 * Complete unified node configurations.
 * This replaces all scattered node configuration across the codebase.
 */
export const UNIFIED_NODE_CONFIGS: Record<NodeType, NodeConfig> = {
  start: {
    label: 'Start',
    description: 'Entry point of the workflow',
    emoji: '🚀',
    borderColor: 'border-green-500',
    width: 200,
    className: 'bg-green-50',
    category: 'flow',
    reactFlowType: 'start',
    blockType: 'start',
    handles: {
      sources: [{
        id: 'default',
        position: 'right',
        label: 'Output',
        color: 'bg-green-500'
      }],
      targets: []
    },
    propertyFields: [
      {
        name: 'output',
        label: 'Output Data',
        type: 'string',
        multiline: true,
        placeholder: 'Enter static data to output',
        isRequired: true
      }
    ],
    defaultData: {
      output: ''
    },
    validation: {
      requiredFields: ['output']
    },
    behavior: {
      allowMultiple: false,
      isRequired: true
    }
  },
  
  condition: {
    label: 'Condition',
    description: 'Branching logic for workflows',
    emoji: '🔀',
    borderColor: 'border-purple-500',
    width: 200,
    className: 'bg-purple-50',
    category: 'control',
    reactFlowType: 'condition',
    blockType: 'condition',
    handles: {
      sources: [
        {
          id: 'true',
          position: 'right',
          offset: { x: 0, y: -15 },
          label: 'True',
          color: 'bg-green-500'
        },
        {
          id: 'false',
          position: 'right',
          offset: { x: 0, y: 15 },
          label: 'False',
          color: 'bg-red-500'
        }
      ],
      targets: [{
        id: 'default',
        position: 'left',
        label: 'Input'
      }]
    },
    propertyFields: [
      {
        name: 'conditionType',
        label: 'Condition Type',
        type: 'select',
        options: [
          { value: 'simple', label: 'Simple Condition' },
          { value: 'complex', label: 'Complex Condition' },
          { value: 'detect_max_iterations', label: 'Detect Max Iterations' }
        ],
        isRequired: true
      },
      {
        name: 'condition',
        label: 'Condition',
        type: 'string',
        placeholder: 'e.g., {{value}} > 10',
        isRequired: true
      }
    ],
    defaultData: {
      conditionType: 'simple',
      condition: ''
    },
    validation: {
      requiredFields: ['conditionType', 'condition']
    }
  },
  
  job: {
    label: 'Job',
    description: 'Execute code in various languages',
    emoji: '⚙️',
    borderColor: 'border-blue-500',
    width: 250,
    className: 'bg-blue-50',
    category: 'data',
    reactFlowType: 'job',
    blockType: 'job',
    handles: {
      sources: [{
        id: 'default',
        position: 'right',
        label: 'Output'
      }],
      targets: [{
        id: 'default',
        position: 'left',
        label: 'Input'
      }]
    },
    propertyFields: [
      {
        name: 'subType',
        label: 'Language',
        type: 'select',
        options: [
          { value: 'python', label: 'Python' },
          { value: 'javascript', label: 'JavaScript' },
          { value: 'bash', label: 'Bash' }
        ],
        isRequired: true
      },
      {
        name: 'code',
        label: 'Code',
        type: 'string',
        multiline: true,
        placeholder: 'Enter your code here...',
        isRequired: true
      }
    ],
    defaultData: {
      subType: 'python',
      code: ''
    },
    validation: {
      requiredFields: ['subType', 'code']
    }
  },
  
  endpoint: {
    label: 'Endpoint',
    description: 'Terminal operations and outputs',
    emoji: '🎯',
    borderColor: 'border-red-500',
    width: 200,
    className: 'bg-red-50',
    category: 'flow',
    reactFlowType: 'endpoint',
    blockType: 'endpoint',
    handles: {
      sources: [],
      targets: [{
        id: 'default',
        position: 'left',
        label: 'Input'
      }]
    },
    propertyFields: [
      {
        name: 'action',
        label: 'Action',
        type: 'select',
        options: [
          { value: 'save', label: 'Save to File' },
          { value: 'output', label: 'Output Result' }
        ],
        isRequired: true
      },
      {
        name: 'filename',
        label: 'Filename',
        type: 'string',
        placeholder: 'output.txt',
        isRequired: false
      }
    ],
    defaultData: {
      action: 'output',
      filename: ''
    },
    validation: {
      requiredFields: ['action']
    }
  },
  
  person_job: {
    label: 'Person Job',
    description: 'LLM API calls with memory',
    emoji: '🤖',
    borderColor: 'border-indigo-500',
    width: 300,
    className: 'bg-indigo-50',
    category: 'llm',
    reactFlowType: 'person_job',
    blockType: 'person_job',
    handles: {
      sources: [{
        id: 'default',
        position: 'right',
        label: 'Output'
      }],
      targets: [
        {
          id: 'first',
          position: 'left',
          offset: { x: 0, y: -15 },
          label: 'First',
          color: 'bg-blue-500'
        },
        {
          id: 'default',
          position: 'left',
          offset: { x: 0, y: 15 },
          label: 'Default',
          color: 'bg-gray-500'
        }
      ]
    },
    propertyFields: [
      {
        name: 'personId',
        label: 'Person',
        type: 'person',
        placeholder: 'Select person...',
        isRequired: true
      },
      {
        name: 'iterationCount',
        label: 'Max Iterations',
        type: 'number',
        min: 1,
        max: 100,
        isRequired: true
      },
      {
        name: 'firstOnlyPrompt',
        label: 'First Iteration Prompt',
        type: 'string',
        multiline: true,
        placeholder: 'Prompt for first iteration (uses "first" input)',
        isRequired: true
      },
      {
        name: 'defaultPrompt',
        label: 'Default Prompt',
        type: 'string',
        multiline: true,
        placeholder: 'Prompt for subsequent iterations (uses "default" input)',
        isRequired: true
      },
      {
        name: 'contextCleaningRule',
        label: 'Context Cleaning',
        type: 'select',
        options: [
          { value: 'none', label: 'No Cleaning' },
          { value: 'trim', label: 'Trim Old Messages' },
          { value: 'summarize', label: 'Summarize Context' }
        ],
        isRequired: true
      }
    ],
    defaultData: {
      personId: '',
      iterationCount: 1,
      firstOnlyPrompt: '',
      defaultPrompt: '',
      contextCleaningRule: 'none'
    },
    validation: {
      requiredFields: ['personId', 'iterationCount', 'firstOnlyPrompt', 'defaultPrompt']
    }
  },
  
  person_batch_job: {
    label: 'Person Batch Job',
    description: 'Batch LLM operations',
    emoji: '🤖🔁',
    borderColor: 'border-indigo-600',
    width: 300,
    className: 'bg-indigo-100',
    category: 'llm',
    reactFlowType: 'person_batch_job',
    blockType: 'person_batch_job',
    handles: {
      sources: [{
        id: 'default',
        position: 'right',
        label: 'Output'
      }],
      targets: [{
        id: 'default',
        position: 'left',
        label: 'Input'
      }]
    },
    propertyFields: [
      {
        name: 'personId',
        label: 'Person',
        type: 'person',
        placeholder: 'Select person...',
        isRequired: true
      },
      {
        name: 'prompt',
        label: 'Prompt Template',
        type: 'string',
        multiline: true,
        placeholder: 'Process: {{item}}',
        isRequired: true
      },
      {
        name: 'batchSize',
        label: 'Batch Size',
        type: 'number',
        min: 1,
        max: 100,
        isRequired: true
      }
    ],
    defaultData: {
      personId: '',
      prompt: '',
      batchSize: 10
    },
    validation: {
      requiredFields: ['personId', 'prompt', 'batchSize']
    }
  },
  
  db: {
    label: 'Database',
    description: 'Data operations and file I/O',
    emoji: '💾',
    borderColor: 'border-yellow-500',
    width: 250,
    className: 'bg-yellow-50',
    category: 'data',
    reactFlowType: 'db',
    blockType: 'db',
    handles: {
      sources: [{
        id: 'default',
        position: 'bottom',
        label: 'Output'
      }],
      targets: [{
        id: 'default',
        position: 'top',
        label: 'Input'
      }]
    },
    propertyFields: [
      {
        name: 'operation',
        label: 'Operation',
        type: 'select',
        options: [
          { value: 'read', label: 'Read File' },
          { value: 'write', label: 'Write File' },
          { value: 'query', label: 'Query Database' }
        ],
        isRequired: true
      },
      {
        name: 'path',
        label: 'File Path',
        type: 'string',
        placeholder: 'data/file.json',
        isRequired: true
      },
      {
        name: 'format',
        label: 'Format',
        type: 'select',
        options: [
          { value: 'json', label: 'JSON' },
          { value: 'csv', label: 'CSV' },
          { value: 'text', label: 'Text' }
        ],
        isRequired: true
      }
    ],
    defaultData: {
      operation: 'read',
      path: '',
      format: 'json'
    },
    validation: {
      requiredFields: ['operation', 'path', 'format']
    },
    behavior: {
      verticalHandles: true
    }
  },
  
  user_response: {
    label: 'User Response',
    description: 'Interactive prompt for user input',
    emoji: '❓',
    borderColor: 'border-indigo-500',
    width: 250,
    className: 'bg-indigo-50',
    category: 'control',
    reactFlowType: 'user_response',
    blockType: 'user_response',
    handles: {
      sources: [{
        id: 'default',
        position: 'right',
        label: 'Output'
      }],
      targets: [{
        id: 'default',
        position: 'left',
        label: 'Input'
      }]
    },
    propertyFields: [
      {
        name: 'promptMessage',
        label: 'Prompt Message',
        type: 'string',
        multiline: true,
        placeholder: 'Enter the message to display to the user...',
        isRequired: true
      },
      {
        name: 'timeoutSeconds',
        label: 'Timeout (seconds)',
        type: 'number',
        min: 1,
        max: 60,
        placeholder: '10',
        helperText: 'Time to wait for user response (default: 10)'
      }
    ],
    defaultData: {
      promptMessage: '',
      timeoutSeconds: 10
    },
    validation: {
      requiredFields: ['promptMessage']
    }
  },
  
  notion: {
    label: 'Notion',
    description: 'Interact with Notion API',
    emoji: '📄',
    borderColor: 'border-gray-500',
    width: 300,
    className: 'bg-gray-50',
    category: 'data',
    reactFlowType: 'notion',
    blockType: 'notion',
    handles: {
      sources: [{
        id: 'default',
        position: 'right',
        label: 'Output'
      }],
      targets: [{
        id: 'default',
        position: 'left',
        label: 'Input'
      }]
    },
    propertyFields: [
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
          { value: 'extract_text', label: 'Extract Text' }
        ],
        isRequired: true
      },
      {
        name: 'apiKeyId',
        label: 'API Key',
        type: 'string',
        placeholder: 'Select API key...',
        isRequired: true
      },
      {
        name: 'pageId',
        label: 'Page ID',
        type: 'string',
        placeholder: 'Notion page ID'
      },
      {
        name: 'blockId',
        label: 'Block ID',
        type: 'string',
        placeholder: 'Notion block ID'
      },
      {
        name: 'databaseId',
        label: 'Database ID',
        type: 'string',
        placeholder: 'Notion database ID'
      }
    ],
    defaultData: {
      operation: 'read_page',
      apiKeyId: '',
      pageId: '',
      blockId: '',
      databaseId: ''
    },
    validation: {
      requiredFields: ['operation', 'apiKeyId']
    }
  }
};

// Helper functions to work with the unified config
export const getNodeConfig = (nodeType: NodeType): NodeConfig => {
  return UNIFIED_NODE_CONFIGS[nodeType];
};

export const getNodeHandles = (nodeType: NodeType) => {
  const config = getNodeConfig(nodeType);
  return config.handles;
};

export const getNodeDefaults = (nodeType: NodeType) => {
  const config = getNodeConfig(nodeType);
  return config.defaultData;
};

export const getNodePropertyFields = (nodeType: NodeType) => {
  const config = getNodeConfig(nodeType);
  return config.propertyFields;
};

export const validateNodeData = (nodeType: NodeType, data: unknown) => {
  const config = getNodeConfig(nodeType);
  const errors: string[] = [];
  const nodeData = data as Record<string, unknown>;
  
  if (config.validation) {
    // Check required fields
    for (const field of config.validation.requiredFields) {
      if (!nodeData[field]) {
        errors.push(`${field} is required`);
      }
    }
    
    // Run custom validation if available
    if (config.validation.customValidation) {
      const customResult = config.validation.customValidation(data);
      if (!customResult.valid && customResult.errors) {
        errors.push(...customResult.errors);
      }
    }
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
};

// Helper functions for React Flow type mapping
export const getReactFlowType = (blockType: string): string => {
  const config = Object.values(UNIFIED_NODE_CONFIGS).find(c => c.blockType === blockType);
  return config?.reactFlowType || blockType;
};

export const getBlockType = (reactFlowType: string): string => {
  const config = Object.values(UNIFIED_NODE_CONFIGS).find(c => c.reactFlowType === reactFlowType);
  return config?.blockType || reactFlowType;
};

export const getUnifiedNodeConfigsByReactFlowType = () => {
  return Object.fromEntries(
    Object.entries(UNIFIED_NODE_CONFIGS).map(([_, config]) => [config.reactFlowType, config])
  );
};