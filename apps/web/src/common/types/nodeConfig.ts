// Unified node configuration system
import { Position } from '@xyflow/react';

// Handle color constants for consistency
export const HANDLE_COLORS = {
  green: '#059669',    // green-600
  purple: '#9333ea',   // purple-600
  teal: '#0d9488',     // teal-600
  orange: '#ea580c',   // orange-600
  blue: '#2563eb',     // blue-600
  red: '#dc2626',      // red-600
  indigo: '#4f46e5',   // indigo-600
  amber: '#d97706',    // amber-600
} as const;

export interface HandleConfig {
  type: 'input' | 'output';
  position: Position;
  name: string;
  offset: number; // Percentage from top (0-100)
  color: string;
}

export interface FieldConfig {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'number' | 'select' | 'checkbox';
  placeholder?: string;
  isRequired?: boolean;
  options?: { value: string; label: string }[];
  rows?: number;
  hint?: string;
}

export interface UnifiedNodeConfig {
  // Visual configuration
  handles: HandleConfig[];
  borderColor: string;
  width: string;
  className?: string;
  emoji: string;
  label: string;
  
  // React Flow mapping
  reactFlowType: string;
  blockType: string;
  
  // Properties configuration
  propertyFields: FieldConfig[];
  propertyTitle: string;
  
  // Additional metadata
  description?: string;
  category?: 'control' | 'processing' | 'data' | 'output';
}

export const UNIFIED_NODE_CONFIGS: Record<string, UnifiedNodeConfig> = {
  start: {
    // Visual config
    handles: [
      { type: 'output', position: Position.Right, name: 'default', offset: 50, color: '#059669' }
    ],
    borderColor: 'green',
    width: 'w-20 h-20',
    className: 'rounded-full',
    emoji: '🚀',
    label: 'Start',
    
    // React Flow mapping
    reactFlowType: 'start',
    blockType: 'start',
    
    // Properties config
    propertyTitle: 'Start Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'Start', isRequired: true }
    ],
    
    // Metadata
    description: 'Entry point for the workflow',
    category: 'control'
  },
  
  person_job: {
    // Visual config
    handles: [
      { type: 'input', position: Position.Left, name: 'first', offset: 30, color: '#9333ea' },
      { type: 'input', position: Position.Left, name: 'default', offset: 70, color: '#0d9488' },
      { type: 'output', position: Position.Right, name: 'default', offset: 50, color: '#ea580c' }
    ],
    borderColor: 'blue',
    width: 'w-52',
    emoji: '🤖',
    label: 'Person Job',
    
    // React Flow mapping
    reactFlowType: 'person_job',
    blockType: 'person_job',
    
    // Properties config
    propertyTitle: 'Person Job Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'Enter job name', isRequired: true },
      { name: 'personId', label: 'Person', type: 'select', options: [] }, // Will be populated dynamically
      { name: 'defaultPrompt', label: 'Default Prompt', type: 'textarea', placeholder: 'Enter default prompt', rows: 4 },
      { name: 'firstOnlyPrompt', label: 'First Only Prompt', type: 'textarea', placeholder: 'Enter first only prompt', rows: 4 },
      { name: 'contextCleaningRule', label: 'Context Cleaning', type: 'select', options: [
        { value: 'uponRequest', label: 'Upon Request' },
        { value: 'noForget', label: 'No Forget' },
        { value: 'onEveryTurn', label: 'On Every Turn' }
      ]},
      { name: 'iterationCount', label: 'Max Iterations', type: 'number', placeholder: '1' }
    ],
    
    // Metadata
    description: 'Execute LLM tasks with a configured person',
    category: 'processing'
  },
  
  condition: {
    // Visual config
    handles: [
      { type: 'input', position: Position.Left, name: 'default', offset: 50, color: '#2563eb' },
      { type: 'output', position: Position.Right, name: 'true', offset: 70, color: '#059669' },
      { type: 'output', position: Position.Right, name: 'false', offset: 30, color: '#dc2626' }
    ],
    borderColor: 'yellow',
    width: 'w-48',
    emoji: '🔀',
    label: 'Condition',
    
    // React Flow mapping
    reactFlowType: 'condition',
    blockType: 'condition',
    
    // Properties config
    propertyTitle: 'Condition Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'Enter condition name', isRequired: true },
      { name: 'conditionType', label: 'Condition Type', type: 'select', options: [
        { value: 'expression', label: 'Expression' },
        { value: 'detect_max_iterations', label: 'Detect Max Iterations' }
      ]},
      { name: 'expression', label: 'Expression', type: 'textarea', placeholder: 'Enter condition expression', rows: 3 },
      { name: 'maxIterations', label: 'Detect Max Iterations', type: 'number', placeholder: '10' }
    ],
    
    // Metadata
    description: 'Branch workflow based on conditions',
    category: 'control'
  },
  
  db: {
    // Visual config
    handles: [
      { type: 'input', position: Position.Bottom, name: 'trigger', offset: 30, color: '#4f46e5' },
      { type: 'output', position: Position.Bottom, name: 'data', offset: 70, color: '#d97706' }
    ],
    borderColor: 'purple',
    width: 'w-64',
    emoji: '📊',
    label: 'DB Source',
    
    // React Flow mapping
    reactFlowType: 'db',
    blockType: 'db',
    
    // Properties config
    propertyTitle: 'Database Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'Enter database name', isRequired: true },
      { name: 'subType', label: 'Source Type', type: 'select', options: [
        { value: 'fixed_prompt', label: 'Fixed Prompt' },
        { value: 'file', label: 'File' }
      ]},
      { name: 'sourceDetails', label: 'Source Details', type: 'textarea', placeholder: 'Enter source details', rows: 4 }
    ],
    
    // Metadata
    description: 'Data source for workflow',
    category: 'data'
  },
  
  job: {
    // Visual config
    handles: [
      { type: 'input', position: Position.Left, name: 'first', offset: 30, color: '#9333ea' },
      { type: 'input', position: Position.Left, name: 'default', offset: 70, color: '#0d9488' },
      { type: 'output', position: Position.Right, name: 'default', offset: 50, color: '#ea580c' }
    ],
    borderColor: 'blue',
    width: 'w-48',
    emoji: '⚙️',
    label: 'Job',
    
    // React Flow mapping
    reactFlowType: 'job',
    blockType: 'job',
    
    // Properties config
    propertyTitle: 'Job Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'Enter job name', isRequired: true },
      { name: 'subType', label: 'Job Type', type: 'select', options: [
        { value: 'code', label: 'Code Execution' },
        { value: 'api_tool', label: 'API Tool' },
        { value: 'diagram_link', label: 'Diagram Link' }
      ]},
      { name: 'sourceDetails', label: 'Details', type: 'textarea', placeholder: 'Enter job details...', rows: 8 }
    ],
    
    // Metadata
    description: 'Execute code or call APIs',
    category: 'processing'
  },
  
  person_batch_job: {
    // Visual config
    handles: [
      { type: 'input', position: Position.Left, name: 'batch', offset: 50, color: '#4f46e5' },
      { type: 'output', position: Position.Right, name: 'default', offset: 50, color: '#d97706' }
    ],
    borderColor: 'indigo',
    width: 'w-52',
    emoji: '🤖📦',
    label: 'Person Batch Job',
    
    // React Flow mapping
    reactFlowType: 'person_batch_job',
    blockType: 'person_batch_job',
    
    // Properties config
    propertyTitle: 'Person Batch Job Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'Enter batch job name', isRequired: true },
      { name: 'personId', label: 'Person', type: 'select', options: [] }, // Will be populated dynamically
      { name: 'batchPrompt', label: 'Batch Prompt', type: 'textarea', placeholder: 'Enter batch processing prompt', rows: 4 },
      { name: 'batchSize', label: 'Batch Size', type: 'number', placeholder: '10' },
      { name: 'parallelProcessing', label: 'Parallel Processing', type: 'checkbox' },
      { name: 'aggregationMethod', label: 'Aggregation Method', type: 'select', options: [
        { value: 'concatenate', label: 'Concatenate' },
        { value: 'summarize', label: 'Summarize' },
        { value: 'custom', label: 'Custom' }
      ]},
      { name: 'customAggregationPrompt', label: 'Custom Aggregation Prompt', type: 'textarea', placeholder: 'Enter custom aggregation prompt', rows: 3 },
      { name: 'iterationCount', label: 'Max Iterations', type: 'number', placeholder: '1' }
    ],
    
    // Metadata
    description: 'Process multiple items in batches with LLM',
    category: 'processing'
  },
  
  endpoint: {
    // Visual config
    handles: [
      { type: 'input', position: Position.Left, name: 'default', offset: 50, color: '#dc2626' }
    ],
    borderColor: 'red',
    width: 'w-24 h-24',
    className: 'rounded-lg',
    emoji: '🎯',
    label: 'Endpoint',
    
    // React Flow mapping
    reactFlowType: 'endpoint',
    blockType: 'endpoint',
    
    // Properties config
    propertyTitle: 'Endpoint Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'End', isRequired: true },
      { name: 'saveToFile', label: 'Save to File', type: 'checkbox' },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: 'Enter file path' },
      { name: 'fileFormat', label: 'File Format', type: 'select', options: [
        { value: 'json', label: 'JSON' },
        { value: 'text', label: 'Text' },
        { value: 'csv', label: 'CSV' }
      ]}
    ],
    
    // Metadata
    description: 'End point and output destination',
    category: 'output'
  }
};

// Helper functions
export function getNodeConfig(nodeType: string): UnifiedNodeConfig | undefined {
  return UNIFIED_NODE_CONFIGS[nodeType];
}

export function getReactFlowType(blockType: string): string {
  const config = UNIFIED_NODE_CONFIGS[blockType];
  return config?.reactFlowType || blockType;
}

export function getBlockType(reactFlowType: string): string {
  for (const [blockType, config] of Object.entries(UNIFIED_NODE_CONFIGS)) {
    if (config.reactFlowType === reactFlowType) {
      return blockType;
    }
  }
  return reactFlowType;
}

export function getNodeHandles(nodeType: string, nodeId: string, isFlipped: boolean = false) {
  const config = getNodeConfig(nodeType);
  if (!config) return [];

  return config.handles.map(handle => {
    const isVertical = handle.position === Position.Top || handle.position === Position.Bottom;
    const position = isFlipped && !isVertical
      ? (handle.position === Position.Left ? Position.Right : Position.Left)
      : handle.position;
    
    const style = isVertical 
      ? { left: `${handle.offset}%` }
      : { top: `${handle.offset}%` };
    
    return {
      type: handle.type,
      position,
      id: `${nodeId}-${handle.type}-${handle.name}`,
      style,
      className: handle.color
    };
  });
}

export function getAllNodeTypes(): string[] {
  return Object.keys(UNIFIED_NODE_CONFIGS);
}

export function getNodesByCategory(category: string): string[] {
  return Object.entries(UNIFIED_NODE_CONFIGS)
    .filter(([_, config]) => config.category === category)
    .map(([nodeType]) => nodeType);
}

// Get unified node configs mapped by React Flow type for component usage
export function getUnifiedNodeConfigsByReactFlowType(): Record<string, UnifiedNodeConfig> {
  const mapped: Record<string, UnifiedNodeConfig> = {};
  
  for (const [_blockType, config] of Object.entries(UNIFIED_NODE_CONFIGS)) {
    mapped[config.reactFlowType] = config;
  }
  
  return mapped;
}

