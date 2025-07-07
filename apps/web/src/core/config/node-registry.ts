import { HandleLabel, type NodeType } from '@dipeo/domain-models';
import type { NodeTypeKey } from '@/core/types/type-factories';
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
import type { UnifiedNodeConfig } from './unifiedConfig';
import { NODE_META } from './nodeMeta';

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

/**
 * Node configuration without visual metadata (which comes from NODE_META)
 */
export interface NodeRegistryEntry<T extends Record<string, unknown> = Record<string, unknown>> {
  // Node configuration
  handles?: UnifiedNodeConfig['handles'];
  defaults?: Record<string, unknown>;
  
  // Panel configuration
  panelLayout?: 'single' | 'twoColumn';
  panelFieldOrder?: string[];
  panelFieldOverrides?: Partial<Record<keyof T, Partial<TypedPanelFieldConfig<T>>>>;
  panelCustomFields?: Array<TypedPanelFieldConfig<T>>; // Most fields now in field-registry.ts
}

/**
 * Complete node registry with all configuration
 */
export const NODE_REGISTRY: {
  [K in NodeType]: NodeRegistryEntry<NodeDataTypeMap[K]>
} = {
  start: {
    handles: {
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
    defaults: { label: 'Start', enable_hook: false, hook_type: 'webhook', hook_config: '' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'enable_hook', 'hook_type', 'hook_config'],
    // Field definitions moved to field-registry.ts
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
    handles: {
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [
        { id: HandleLabel.CONDITION_TRUE, position: 'right', label: 'true', offset: { x: 0, y: 30 } },
        { id: HandleLabel.CONDITION_FALSE, position: 'right', label: 'false', offset: { x: 0, y: -30 } }
      ]
    },
    defaults: { label: 'Condition', condition_type: 'custom', expression: '' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'condition_type', 'expression'],
    // Field definitions moved to field-registry.ts
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
          if (formData?.condition_type === 'custom' && (!value || typeof value !== 'string' || value.trim().length === 0)) {
            return { isValid: false, error: 'Expression is required for custom conditions' };
          }
          return { isValid: true };
        }
      }
    }
  },
  
  job: {
    handles: {
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
    defaults: { label: 'Job' }
  },
  
  code_job: {
    handles: {
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
    defaults: { label: 'Code Job', language: 'python', code: '' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'language', 'code'],
    // Field definitions moved to field-registry.ts
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
    handles: {
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
    defaults: { label: 'API Job', url: '', method: 'GET', headers: '', body: '' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'url', 'method', 'headers', 'body'],
    // Field definitions moved to field-registry.ts
    panelFieldOverrides: {
      url: { column: 1 },
      method: { column: 1 },
      headers: { column: 2, rows: 4 },
      body: { column: 2, rows: 6 }
    }
  },
  
  endpoint: {
    handles: {
      input: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
    defaults: { label: 'Endpoint', output_variable: '', save_to_file: false, file_format: 'json', file_name: '' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'output_variable', 'save_to_file', 'file_format', 'file_name'],
    // Field definitions moved to field-registry.ts
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
    handles: {
      input: [
        { id: HandleLabel.FIRST, position: 'left', label: 'first', offset: { x: 0, y: -60 }, color: '#f59e0b' },
        { id: HandleLabel.DEFAULT, position: 'left', label: 'default', offset: { x: 0, y: 60 }, color: '#2563eb' }
      ],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
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
    // Keep only special field type that's not in field-registry
    panelCustomFields: [
      {
        type: 'labelPersonRow',
        labelPlaceholder: 'Person Job'
      }
    ]
  },
  
  person_batch_job: {
    handles: {
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
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
    // Keep special field type
    panelCustomFields: [
      {
        type: 'labelPersonRow',
        labelPlaceholder: 'Person Batch Job'
      }
    ]
  },
  
  db: {
    handles: {
      input: [{ id: HandleLabel.DEFAULT, position: 'bottom', offset: { x: -30, y: 0 } }],
      output: [{ id: HandleLabel.DEFAULT, position: 'bottom', offset: { x: 30, y: 0 } }]
    },
    defaults: { label: 'Database', sub_type: 'fixed_prompt', source_details: '', operation: 'read' },
    panelLayout: 'twoColumn',
    panelFieldOrder: ['label', 'sub_type', 'operation', 'source_details'],
    // Field definitions moved to field-registry.ts
    panelFieldOverrides: {
      label: { column: 1 },
      sub_type: { column: 1 },
      operation: { column: 1 },
      source_details: {
        column: 2,
        rows: 6,
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
    }
  },
  
  user_response: {
    handles: {
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
    defaults: { label: 'User Response', prompt: '' },
    // Field definitions moved to field-registry.ts
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
    handles: {
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
    defaults: { label: 'Notion', page_id: '', operation: 'read' }
  },
  
  hook: {
    handles: {
      input: [{ id: HandleLabel.DEFAULT, position: 'left' }],
      output: [{ id: HandleLabel.DEFAULT, position: 'right' }]
    },
    defaults: { label: 'Hook', hook_type: 'webhook', command: '' }
  }
};

/**
 * Get node configuration for a specific type
 */
export function getNodeRegistryEntry(nodeType: NodeType): NodeRegistryEntry<any> {
  return NODE_REGISTRY[nodeType] as NodeRegistryEntry<any>;
}

/**
 * Create a unified node config from registry entry and NODE_META
 */
export function createNodeConfigFromRegistry(
  nodeType: NodeTypeKey,
  entry: NodeRegistryEntry<any>
): UnifiedNodeConfig<any> {
  const meta = NODE_META[nodeType as NodeType];
  return {
    label: meta.label,
    icon: meta.icon,
    color: meta.color,
    nodeType,
    handles: entry.handles || {},
    defaults: entry.defaults || {},
    panelLayout: entry.panelLayout,
    panelFieldOrder: entry.panelFieldOrder,
    panelFieldOverrides: entry.panelFieldOverrides,
    panelCustomFields: entry.panelCustomFields
  };
}