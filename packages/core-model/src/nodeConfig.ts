// Unified node configuration system
import React from 'react';
import { Position } from '@xyflow/react';

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
  required?: boolean;
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
      { type: 'output', position: Position.Right, name: 'default', offset: 50, color: '!bg-green-600 !border-2 !border-white' }
    ],
    borderColor: 'green',
    width: 'w-28 h-28',
    className: 'rounded-full',
    emoji: '🚀',
    label: 'Start',
    
    // React Flow mapping
    reactFlowType: 'startNode',
    blockType: 'start',
    
    // Properties config
    propertyTitle: 'Start Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'Start', required: true }
    ],
    
    // Metadata
    description: 'Entry point for the workflow',
    category: 'control'
  },
  
  person_job: {
    // Visual config
    handles: [
      { type: 'input', position: Position.Left, name: 'first', offset: 30, color: '!bg-purple-600 !border-2 !border-white' },
      { type: 'input', position: Position.Left, name: 'default', offset: 70, color: '!bg-teal-600 !border-2 !border-white' },
      { type: 'output', position: Position.Right, name: 'default', offset: 50, color: '!bg-orange-600 !border-2 !border-white' }
    ],
    borderColor: 'blue',
    width: 'w-52',
    emoji: '🤖',
    label: 'Person Job',
    
    // React Flow mapping
    reactFlowType: 'personjobNode',
    blockType: 'person_job',
    
    // Properties config
    propertyTitle: 'Person Job Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'Enter job name', required: true },
      { name: 'personId', label: 'Person', type: 'select', options: [] }, // Will be populated dynamically
      { name: 'defaultPrompt', label: 'Default Prompt', type: 'textarea', placeholder: 'Enter default prompt', rows: 4 },
      { name: 'firstOnlyPrompt', label: 'First Only Prompt', type: 'textarea', placeholder: 'Enter first only prompt', rows: 4 },
      { name: 'mode', label: 'Mode', type: 'select', options: [
        { value: 'sync', label: 'Synchronous' },
        { value: 'batch', label: 'Batch' }
      ]},
      { name: 'contextCleaningRule', label: 'Context Cleaning', type: 'select', options: [
        { value: 'upon_request', label: 'Upon Request' },
        { value: 'no_forget', label: 'No Forget' },
        { value: 'on_every_turn', label: 'On Every Turn' }
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
      { type: 'input', position: Position.Left, name: 'default', offset: 50, color: '!bg-blue-600 !border-2 !border-white' },
      { type: 'output', position: Position.Right, name: 'true', offset: 70, color: '!bg-green-600 !border-2 !border-white' },
      { type: 'output', position: Position.Right, name: 'false', offset: 30, color: '!bg-red-600 !border-2 !border-white' }
    ],
    borderColor: 'yellow',
    width: 'w-48',
    emoji: '🔀',
    label: 'Condition',
    
    // React Flow mapping
    reactFlowType: 'conditionNode',
    blockType: 'condition',
    
    // Properties config
    propertyTitle: 'Condition Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'Enter condition name', required: true },
      { name: 'conditionType', label: 'Condition Type', type: 'select', options: [
        { value: 'expression', label: 'Expression' },
        { value: 'max_iterations', label: 'Max Iterations' }
      ]},
      { name: 'expression', label: 'Expression', type: 'textarea', placeholder: 'Enter condition expression', rows: 3 },
      { name: 'maxIterations', label: 'Max Iterations', type: 'number', placeholder: '10' }
    ],
    
    // Metadata
    description: 'Branch workflow based on conditions',
    category: 'control'
  },
  
  db: {
    // Visual config
    handles: [
      { type: 'input', position: Position.Bottom, name: 'trigger', offset: 30, color: '!bg-indigo-600 !border-2 !border-white' },
      { type: 'output', position: Position.Bottom, name: 'data', offset: 70, color: '!bg-amber-600 !border-2 !border-white' }
    ],
    borderColor: 'purple',
    width: 'w-64',
    emoji: '📊',
    label: 'DB Source',
    
    // React Flow mapping
    reactFlowType: 'dbNode',
    blockType: 'db',
    
    // Properties config
    propertyTitle: 'Database Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'Enter database name', required: true },
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
      { type: 'input', position: Position.Left, name: 'job', offset: 50, color: '!bg-blue-600 !border-2 !border-white' },
      { type: 'output', position: Position.Right, name: 'job', offset: 50, color: '!bg-green-600 !border-2 !border-white' }
    ],
    borderColor: 'blue',
    width: 'w-48',
    emoji: '⚙️',
    label: 'Job',
    
    // React Flow mapping
    reactFlowType: 'jobNode',
    blockType: 'job',
    
    // Properties config
    propertyTitle: 'Job Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'Enter job name', required: true },
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
  
  endpoint: {
    // Visual config
    handles: [
      { type: 'input', position: Position.Left, name: 'default', offset: 50, color: '!bg-red-600 !border-2 !border-white' }
    ],
    borderColor: 'red',
    width: 'w-40 h-40',
    className: 'rounded-lg',
    emoji: '🎯',
    label: 'Endpoint',
    
    // React Flow mapping
    reactFlowType: 'endpointNode',
    blockType: 'endpoint',
    
    // Properties config
    propertyTitle: 'Endpoint Properties',
    propertyFields: [
      { name: 'label', label: 'Label', type: 'text', placeholder: 'End', required: true },
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

// Legacy compatibility function for old NodeConfig format
export function getLegacyNodeConfigs(): Record<string, {
  handles: HandleConfig[];
  borderColor: string;
  width: string;
  className?: string;
  emoji?: string;
}> {
  const legacy: Record<string, any> = {};
  
  for (const [blockType, config] of Object.entries(UNIFIED_NODE_CONFIGS)) {
    legacy[config.reactFlowType] = {
      handles: config.handles,
      borderColor: config.borderColor,
      width: config.width,
      className: config.className,
      emoji: config.emoji
    };
  }
  
  return legacy;
}

// Legacy types from diagram-ui for backwards compatibility
export interface NodeConfig {
  handles: HandleConfig[];
  borderColor: string;
  width: string;
  className?: string;
  emoji?: string;
}

export interface BaseNodeProps extends React.HTMLAttributes<HTMLDivElement> {
  id: string;
  children: React.ReactNode;
  selected?: boolean;
  onFlip?: () => void;
  handles?: {
    type: 'input' | 'output';
    position: Position;
    id?: string;
    style?: React.CSSProperties;
    className?: string;
  }[];
  borderColor?: string;
  showFlipButton?: boolean;
  nodeType?: string;
  data?: any;
  autoHandles?: boolean;
  isRunning?: boolean;
  onUpdateData?: (nodeId: string, data: any) => void;
  onUpdateNodeInternals?: (nodeId: string) => void;
  nodeConfigs?: Record<string, NodeConfig>;
  // Add the missing properties that were being used
  onDragOver?: React.DragEventHandler<HTMLDivElement>;
  onDrop?: React.DragEventHandler<HTMLDivElement>;
}

export interface GenericNodeProps {
  id: string;
  data: any;
  selected?: boolean;
  nodeType: string;
  children: React.ReactNode;
  showFlipButton?: boolean;
  onDragOver?: React.DOMAttributes<HTMLDivElement>['onDragOver'];
  onDrop?: React.DOMAttributes<HTMLDivElement>['onDrop'];
  isRunning?: boolean;
  onUpdateData?: (nodeId: string, data: any) => void;
  onUpdateNodeInternals?: (nodeId: string) => void;
  nodeConfigs?: Record<string, NodeConfig>;
}

// Legacy types from properties-ui for backwards compatibility
export interface FormFieldProps {
  label: string;
  id?: string;
  children: React.ReactNode;
  className?: string;
}

export interface PanelProps {
  icon?: React.ReactNode;
  title: string;
  children: React.ReactNode;
}

export interface GenericPropertiesPanelProps {
  nodeId: string;
  nodeType: string;
  fields: FieldConfig[];
  title: string;
  icon?: React.ReactNode;
  data?: Record<string, any>;
  onChange?: (nodeId: string, data: Record<string, any>) => void;
}