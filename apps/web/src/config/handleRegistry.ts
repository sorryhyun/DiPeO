export interface HandleDefinition {
  id: string;
  position: 'top' | 'right' | 'bottom' | 'left';
  label?: string;
  offset?: { x?: number; y?: number };
  color?: string;
  // Note: direction is inferred from whether it's in inputs or outputs array
}

export interface NodeHandleConfig {
  inputs?: HandleDefinition[];
  outputs?: HandleDefinition[];
}

// Centralized handle registry for all node types
export const HANDLE_REGISTRY: Record<string, NodeHandleConfig> = {
  'start': {
    outputs: [{ id: 'default', position: 'right' }]
  },
  
  'endpoint': {
    inputs: [{ id: 'default', position: 'left' }]
  },
  
  'condition': {
    inputs: [{ id: 'default', position: 'left' }],
    outputs: [
      { id: 'true', position: 'right', label: 'true', offset: { y: -20 } },
      { id: 'false', position: 'right', label: 'false', offset: { y: 20 } }
    ]
  },
  
  'job': {
    inputs: [{ id: 'default', position: 'left' }],
    outputs: [{ id: 'default', position: 'right' }]
  },
  
  'person_job': {
    inputs: [
      { id: 'first', position: 'left', label: 'first', offset: { y: -40 } },
      { id: 'default', position: 'left', label: 'default', offset: { y: 40 } }
    ],
    outputs: [{ id: 'default', position: 'right' }]
  },
  
  'person_batch_job': {
    inputs: [{ id: 'default', position: 'left' }],
    outputs: [{ id: 'default', position: 'right' }]
  },
  
  'db': {
    inputs: [{ id: 'default', position: 'bottom' }],
    outputs: [{ id: 'default', position: 'bottom' }]
  },
  
  'user_response': {
    inputs: [{ id: 'default', position: 'left' }],
    outputs: [{ id: 'default', position: 'right' }]
  },
  
  'notion': {
    inputs: [{ id: 'default', position: 'left' }],
    outputs: [{ id: 'default', position: 'right' }]
  }
};

// Helper function to get handle config for a node type
export function getHandleConfig(nodeType: string): NodeHandleConfig {
  return HANDLE_REGISTRY[nodeType] || { inputs: [], outputs: [] };
}

// Helper to validate if a handle exists for a node type
export function hasHandle(nodeType: string, handleId: string, isInput: boolean): boolean {
  const config = getHandleConfig(nodeType);
  const handles = isInput ? config.inputs : config.outputs;
  return handles?.some(h => h.id === handleId) ?? false;
}