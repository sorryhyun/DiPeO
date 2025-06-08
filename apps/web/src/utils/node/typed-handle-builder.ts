// apps/web/src/utils/node/typed-handle-builder.ts
import { NodeBase, InputHandle, OutputHandle } from '@/types/node-base';
import { DiagramNode } from '@/types/nodes';
import { handleId, nodeId } from '@/types/branded';
import { HANDLE_REGISTRY } from '@/config/handleRegistry';

/**
 * Builds typed handles for a node based on the handle registry
 * This ensures type safety and consistency across the application
 */
export function buildNodeHandles<N extends DiagramNode>(
  node: Omit<N, 'inputs' | 'outputs'>
): N {
  const nodeType = node.type;
  const handleConfig = HANDLE_REGISTRY[nodeType];
  
  if (!handleConfig) {
    console.warn(`No handle configuration found for node type: ${nodeType}`);
    return { ...node, inputs: {}, outputs: {} } as N;
  }
  
  // Build input handles
  const inputs = {} as N['inputs'];
  if (handleConfig.inputs) {
    for (const config of handleConfig.inputs) {
      const handle: InputHandle<string> = {
        id: handleId(`${node.id}:${config.id}`),
        kind: 'input',
        name: config.id,
        dataType: 'any', // Default to 'any' for now
        label: config.label,
        position: { 
          x: config.position === 'left' ? 0 : config.position === 'right' ? 1 : 0.5,
          y: config.position === 'top' ? 0 : config.position === 'bottom' ? 1 : 0.5
        }
      };
      
      // Apply offset if provided
      if (config.offset) {
        handle.position = {
          x: handle.position.x + (config.offset.x || 0),
          y: handle.position.y + (config.offset.y || 0)
        };
      }
      
      (inputs as any)[config.id] = handle;
    }
  }
  
  // Build output handles
  const outputs = {} as N['outputs'];
  if (handleConfig.outputs) {
    for (const config of handleConfig.outputs) {
      const handle: OutputHandle<string> = {
        id: handleId(`${node.id}:${config.id}`),
        kind: 'output',
        name: config.id,
        dataType: 'any', // Default to 'any' for now
        label: config.label,
        position: {
          x: config.position === 'left' ? 0 : config.position === 'right' ? 1 : 0.5,
          y: config.position === 'top' ? 0 : config.position === 'bottom' ? 1 : 0.5
        }
      };
      
      // Apply offset if provided
      if (config.offset) {
        handle.position = {
          x: handle.position.x + (config.offset.x || 0),
          y: handle.position.y + (config.offset.y || 0)
        };
      }
      
      (outputs as any)[config.id] = handle;
    }
  }
  
  return { ...node, inputs, outputs } as N;
}

/**
 * Creates a new node with typed handles
 */
export function createTypedNode<T extends DiagramNode['type']>(
  type: T,
  position: { x: number; y: number },
  data: Omit<Extract<DiagramNode, { type: T }>['data'], 'id' | 'type'>
): Extract<DiagramNode, { type: T }> {
  const id = nodeId(generateNodeId());
  
  const nodeData = {
    ...data,
    id,
    type
  } as Extract<DiagramNode, { type: T }>['data'];
  
  const node = {
    id,
    type,
    position,
    data: nodeData
  } as Omit<Extract<DiagramNode, { type: T }>, 'inputs' | 'outputs'>;
  
  return buildNodeHandles(node);
}

/**
 * Helper to generate a unique node ID
 */
function generateNodeId(): string {
  return `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Type-safe handle accessor
 */
export function getHandle<
  N extends DiagramNode,
  K extends 'inputs' | 'outputs',
  H extends keyof N[K]
>(node: N, kind: K, handleName: H): N[K][H] {
  return node[kind][handleName];
}

/**
 * Check if a handle exists on a node
 */
export function hasTypedHandle<
  N extends DiagramNode,
  K extends 'inputs' | 'outputs'
>(node: N, kind: K, handleName: string): boolean {
  return handleName in node[kind];
}