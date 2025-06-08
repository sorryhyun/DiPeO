// apps/web/src/utils/connection-helpers.ts
import { ArrowID, HandleID, arrowId, handleId } from '@/types/branded';
import { NodeType, DataType } from '@/types/enums';
import { DiagramNode } from '@/types/nodes';
import { OutputHandleNamesOf, InputHandleNamesOf } from '@/types/node-specs';
import { generateShortId } from '@/utils/id';
import { getOutputHandle, getInputHandle } from './handle-utils';

/**
 * Arrow data structure
 */
export interface TypedArrow {
  id: ArrowID;
  source: HandleID;
  target: HandleID;
  type?: 'default' | 'straight' | 'step' | 'smoothstep' | 'bezier';
  animated?: boolean;
  label?: string;
}

/**
 * Connection validation error
 */
export class ConnectionValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConnectionValidationError';
  }
}

/**
 * Check if two data types are compatible for connection
 */
export function areDataTypesCompatible(sourceType: DataType, targetType: DataType): boolean {
  // 'any' type is compatible with everything
  if (sourceType === DataType.Any || targetType === DataType.Any) {
    return true;
  }
  
  // Same type is always compatible
  if (sourceType === targetType) {
    return true;
  }
  
  // Additional compatibility rules
  const compatibilityMap: Record<DataType, DataType[]> = {
    [DataType.String]: [DataType.Text],
    [DataType.Text]: [DataType.String],
    [DataType.Number]: [DataType.Integer, DataType.Float],
    [DataType.Integer]: [DataType.Number, DataType.Float],
    [DataType.Float]: [DataType.Number, DataType.Integer],
    [DataType.JSON]: [DataType.Object, DataType.Array],
    [DataType.Object]: [DataType.JSON],
    [DataType.Array]: [DataType.JSON],
    [DataType.Boolean]: [],
    [DataType.Any]: [] // Already handled above
  };
  
  return compatibilityMap[sourceType]?.includes(targetType) || false;
}

/**
 * Create a connection between two nodes with full type safety
 */
export function connect<
  FromNode extends DiagramNode,
  FromHandle extends OutputHandleNamesOf<FromNode['type']>,
  ToNode extends DiagramNode,
  ToHandle extends InputHandleNamesOf<ToNode['type']>
>(
  from: { node: FromNode; handle: FromHandle },
  to: { node: ToNode; handle: ToHandle },
  options?: {
    type?: TypedArrow['type'];
    animated?: boolean;
    label?: string;
    skipValidation?: boolean;
  }
): TypedArrow {
  // Get the actual handles
  const sourceHandle = getOutputHandle(from.node, from.handle);
  const targetHandle = getInputHandle(to.node, to.handle);
  
  // Validate connection compatibility (unless explicitly skipped)
  if (!options?.skipValidation) {
    if (!areDataTypesCompatible(sourceHandle.dataType, targetHandle.dataType)) {
      throw new ConnectionValidationError(
        `Cannot connect ${from.node.type}.${from.handle} (${sourceHandle.dataType}) ` +
        `to ${to.node.type}.${to.handle} (${targetHandle.dataType})`
      );
    }
  }
  
  // Create the arrow
  return {
    id: arrowId(`ar-${generateShortId()}`),
    source: sourceHandle.id,
    target: targetHandle.id,
    type: options?.type || 'smoothstep',
    animated: options?.animated,
    label: options?.label
  };
}

/**
 * Create multiple connections at once
 */
export function connectMany(
  connections: Array<{
    from: { node: DiagramNode; handle: string };
    to: { node: DiagramNode; handle: string };
    options?: Parameters<typeof connect>[2];
  }>
): TypedArrow[] {
  return connections.map(({ from, to, options }) =>
    connect(from as any, to as any, options)
  );
}

/**
 * Check if a connection is valid without creating it
 */
export function canConnect<
  FromNode extends DiagramNode,
  FromHandle extends OutputHandleNamesOf<FromNode['type']>,
  ToNode extends DiagramNode,
  ToHandle extends InputHandleNamesOf<ToNode['type']>
>(
  from: { node: FromNode; handle: FromHandle },
  to: { node: ToNode; handle: ToHandle }
): boolean {
  try {
    const sourceHandle = getOutputHandle(from.node, from.handle);
    const targetHandle = getInputHandle(to.node, to.handle);
    return areDataTypesCompatible(sourceHandle.dataType, targetHandle.dataType);
  } catch {
    return false;
  }
}

/**
 * Find all valid connections from a source handle
 */
export function findValidTargets(
  sourceNode: DiagramNode,
  sourceHandle: string,
  targetNodes: DiagramNode[]
): Array<{ node: DiagramNode; handle: string }> {
  const validTargets: Array<{ node: DiagramNode; handle: string }> = [];
  
  try {
    const source = getOutputHandle(sourceNode, sourceHandle as any);
    
    for (const targetNode of targetNodes) {
      // Skip self-connections
      if (targetNode.id === sourceNode.id) continue;
      
      // Check each input handle
      for (const handleName of Object.keys(targetNode.inputs)) {
        const targetHandle = targetNode.inputs[handleName as keyof typeof targetNode.inputs];
        if (targetHandle && areDataTypesCompatible(source.dataType, targetHandle.dataType)) {
          validTargets.push({ node: targetNode, handle: handleName });
        }
      }
    }
  } catch {
    // Invalid source handle
  }
  
  return validTargets;
}

/**
 * Find all valid connections from a target handle
 */
export function findValidSources(
  targetNode: DiagramNode,
  targetHandle: string,
  sourceNodes: DiagramNode[]
): Array<{ node: DiagramNode; handle: string }> {
  const validSources: Array<{ node: DiagramNode; handle: string }> = [];
  
  try {
    const target = getInputHandle(targetNode, targetHandle as any);
    
    for (const sourceNode of sourceNodes) {
      // Skip self-connections
      if (sourceNode.id === targetNode.id) continue;
      
      // Check each output handle
      for (const handleName of Object.keys(sourceNode.outputs)) {
        const sourceHandle = sourceNode.outputs[handleName as keyof typeof sourceNode.outputs];
        if (sourceHandle && areDataTypesCompatible(sourceHandle.dataType, target.dataType)) {
          validSources.push({ node: sourceNode, handle: handleName });
        }
      }
    }
  } catch {
    // Invalid target handle
  }
  
  return validSources;
}

/**
 * Create a chain of connections
 */
export function connectChain(
  nodes: DiagramNode[],
  handlePairs?: Array<{ from: string; to: string }>
): TypedArrow[] {
  if (nodes.length < 2) {
    return [];
  }
  
  const arrows: TypedArrow[] = [];
  
  for (let i = 0; i < nodes.length - 1; i++) {
    const fromNode = nodes[i];
    const toNode = nodes[i + 1];
    
    // Use provided handle names or defaults
    const fromHandle = handlePairs?.[i]?.from || 'default';
    const toHandle = handlePairs?.[i]?.to || 'default';
    
    try {
      const arrow = connect(
        { node: fromNode, handle: fromHandle } as any,
        { node: toNode, handle: toHandle } as any
      );
      arrows.push(arrow);
    } catch (error) {
      console.warn(`Failed to connect ${fromNode.id} to ${toNode.id}:`, error);
    }
  }
  
  return arrows;
}

/**
 * Helper to create a connection from handle IDs
 */
export function connectByHandleIds(
  sourceHandleId: HandleID,
  targetHandleId: HandleID,
  options?: {
    type?: TypedArrow['type'];
    animated?: boolean;
    label?: string;
  }
): TypedArrow {
  return {
    id: arrowId(`ar-${generateShortId()}`),
    source: sourceHandleId,
    target: targetHandleId,
    type: options?.type || 'smoothstep',
    animated: options?.animated,
    label: options?.label
  };
}