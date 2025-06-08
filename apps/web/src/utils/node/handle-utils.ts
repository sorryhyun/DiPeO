// apps/web/src/utils/handle-utils.ts
import { NodeID, HandleID, handleId } from '@/types/branded';
import { NodeType } from '@/types/enums';
import { NodeSpecs, HandleNamesOf, InputHandleNamesOf, OutputHandleNamesOf } from '@/types/node-specs';
import { DiagramNode } from '@/types/nodes';
import { InputHandle, OutputHandle } from '@/types/node-base';

/**
 * Error thrown when a handle is not found
 */
export class HandleNotFoundError extends Error {
  constructor(nodeId: NodeID, handleName: string) {
    super(`Handle "${handleName}" not found on node ${nodeId}`);
    this.name = 'HandleNotFoundError';
  }
}

/**
 * Get a specific input handle from a node
 */
export function getInputHandle<
  N extends DiagramNode,
  H extends InputHandleNamesOf<N['type']>
>(
  node: N,
  handleName: H
): InputHandle<H> {
  const handle = node.inputs[handleName as keyof N['inputs']];
  if (!handle) {
    throw new HandleNotFoundError(node.id, handleName);
  }
  return handle as InputHandle<H>;
}

/**
 * Get a specific output handle from a node
 */
export function getOutputHandle<
  N extends DiagramNode,
  H extends OutputHandleNamesOf<N['type']>
>(
  node: N,
  handleName: H
): OutputHandle<H> {
  const handle = node.outputs[handleName as keyof N['outputs']];
  if (!handle) {
    throw new HandleNotFoundError(node.id, handleName);
  }
  return handle as OutputHandle<H>;
}

/**
 * Get all input handles from a node
 */
export function getInputHandles<N extends DiagramNode>(
  node: N
): InputHandle<InputHandleNamesOf<N['type']>>[] {
  return Object.values(node.inputs) as InputHandle<InputHandleNamesOf<N['type']>>[];
}

/**
 * Get all output handles from a node
 */
export function getOutputHandles<N extends DiagramNode>(
  node: N
): OutputHandle<OutputHandleNamesOf<N['type']>>[] {
  return Object.values(node.outputs) as OutputHandle<OutputHandleNamesOf<N['type']>>[];
}

/**
 * Check if a node has a specific input handle
 */
export function hasInputHandle<
  N extends DiagramNode,
  H extends string
>(
  node: N,
  handleName: H
): handleName is InputHandleNamesOf<N['type']> {
  return handleName in node.inputs;
}

/**
 * Check if a node has a specific output handle
 */
export function hasOutputHandle<
  N extends DiagramNode,
  H extends string
>(
  node: N,
  handleName: H
): handleName is OutputHandleNamesOf<N['type']> {
  return handleName in node.outputs;
}

/**
 * Get handle ID from node and handle name
 */
export function getHandleId(nodeId: NodeID, handleName: string): HandleID {
  return handleId(nodeId, handleName);
}

/**
 * Find handle by ID in a node
 */
export function findHandleById<N extends DiagramNode>(
  node: N,
  handleId: HandleID
): InputHandle<string> | OutputHandle<string> | undefined {
  // Check inputs
  for (const handle of Object.values(node.inputs)) {
    if (handle.id === handleId) {
      return handle as InputHandle<string>;
    }
  }
  
  // Check outputs
  for (const handle of Object.values(node.outputs)) {
    if (handle.id === handleId) {
      return handle as OutputHandle<string>;
    }
  }
  
  return undefined;
}

/**
 * Get all handles (both input and output) from a node
 */
export function getAllHandles<N extends DiagramNode>(
  node: N
): Array<InputHandle<string> | OutputHandle<string>> {
  return [
    ...getInputHandles(node),
    ...getOutputHandles(node)
  ];
}

/**
 * Count handles on a node
 */
export function countHandles(node: DiagramNode): {
  inputs: number;
  outputs: number;
  total: number;
} {
  const inputCount = Object.keys(node.inputs).length;
  const outputCount = Object.keys(node.outputs).length;
  
  return {
    inputs: inputCount,
    outputs: outputCount,
    total: inputCount + outputCount
  };
}

/**
 * Get handle names for a specific node type
 */
export function getHandleNamesForType<K extends NodeType>(
  nodeType: K
): {
  inputs: InputHandleNamesOf<K>[];
  outputs: OutputHandleNamesOf<K>[];
} {
  const spec = NodeSpecs[nodeType];
  if (!spec) {
    return { inputs: [], outputs: [] };
  }
  
  const inputs: InputHandleNamesOf<K>[] = [];
  const outputs: OutputHandleNamesOf<K>[] = [];
  
  for (const [name, handle] of Object.entries(spec.handles)) {
    if (handle.direction === 'input') {
      inputs.push(name as InputHandleNamesOf<K>);
    } else {
      outputs.push(name as OutputHandleNamesOf<K>);
    }
  }
  
  return { inputs, outputs };
}

/**
 * Validate if a handle name is valid for a node type
 */
export function isValidHandleName(
  nodeType: NodeType,
  handleName: string,
  direction: 'input' | 'output'
): boolean {
  const spec = NodeSpecs[nodeType];
  if (!spec) return false;
  
  const handle = spec.handles[handleName as keyof typeof spec.handles];
  return handle !== undefined && handle.direction === direction;
}

/**
 * Get handle position offset for visual alignment
 */
export function getHandleOffset(
  nodeType: NodeType,
  handleName: string
): { x: number; y: number } | undefined {
  // Special offsets for specific handles
  const offsetMap: Record<string, Record<string, { x: number; y: number }>> = {
    [NodeType.Condition]: {
      'true': { x: 0, y: -20 },
      'false': { x: 0, y: 20 }
    },
    [NodeType.PersonJob]: {
      'first': { x: 0, y: -20 },
      'default': { x: 0, y: 20 }
    }
  };
  
  return offsetMap[nodeType]?.[handleName];
}