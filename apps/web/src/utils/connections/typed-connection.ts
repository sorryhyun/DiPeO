import { ArrowID, HandleID } from '@/types/branded';
import { Arrow, areDataTypesCompatible } from '@/types/arrow';
import { DiagramNode } from '@/types/diagram';
import { NodeType, ArrowType } from '@/types/enums';
import { InputHandleNamesOf, OutputHandleNamesOf } from '@/types/node-specs';
import { generateId } from '@/utils/id';

// Error types for connection validation
export class ConnectionError extends Error {
  constructor(
    message: string,
    public readonly fromNode: string,
    public readonly fromHandle: string,
    public readonly toNode: string,
    public readonly toHandle: string
  ) {
    super(message);
    this.name = 'ConnectionError';
  }
}

// Create a typed connection between two nodes
export function createConnection<
  FromType extends NodeType,
  ToType extends NodeType,
  FromHandle extends OutputHandleNamesOf<FromType>,
  ToHandle extends InputHandleNamesOf<ToType>
>(
  from: DiagramNode & { type: FromType },
  fromHandle: FromHandle,
  to: DiagramNode & { type: ToType },
  toHandle: ToHandle
): Arrow {
  // Get the output handle from the source node
  const outputHandle = from.outputs[fromHandle as keyof typeof from.outputs];
  if (!outputHandle) {
    throw new ConnectionError(
      `Output handle "${String(fromHandle)}" not found on node "${from.id}"`,
      from.id,
      String(fromHandle),
      to.id,
      String(toHandle)
    );
  }

  // Get the input handle from the target node
  const inputHandle = to.inputs[toHandle as keyof typeof to.inputs];
  if (!inputHandle) {
    throw new ConnectionError(
      `Input handle "${String(toHandle)}" not found on node "${to.id}"`,
      from.id,
      String(fromHandle),
      to.id,
      String(toHandle)
    );
  }

  // Validate data type compatibility
  if (!areDataTypesCompatible(outputHandle.dataType, inputHandle.dataType)) {
    throw new ConnectionError(
      `Cannot connect ${outputHandle.dataType} to ${inputHandle.dataType}`,
      from.id,
      String(fromHandle),
      to.id,
      String(toHandle)
    );
  }

  // Create the arrow
  return {
    id: generateId('arrow') as ArrowID,
    source: outputHandle.id,
    target: inputHandle.id,
    type: 'smoothstep' as ArrowType
  };
}

// Validate an existing connection
export function validateConnection(
  arrow: Arrow,
  nodes: Map<string, DiagramNode>
): { valid: boolean; error?: string } {
  // Find nodes that own the handles
  let sourceNode: DiagramNode | undefined;
  let sourceHandleName: string | undefined;
  let targetNode: DiagramNode | undefined;
  let targetHandleName: string | undefined;

  for (const [_, node] of nodes) {
    // Check outputs
    for (const [name, handle] of Object.entries(node.outputs)) {
      if (handle.id === arrow.source) {
        sourceNode = node;
        sourceHandleName = name;
      }
    }

    // Check inputs
    for (const [name, handle] of Object.entries(node.inputs)) {
      if (handle.id === arrow.target) {
        targetNode = node;
        targetHandleName = name;
      }
    }

    if (sourceNode && targetNode) break;
  }

  if (!sourceNode || !sourceHandleName) {
    return { valid: false, error: `Source handle ${arrow.source} not found` };
  }

  if (!targetNode || !targetHandleName) {
    return { valid: false, error: `Target handle ${arrow.target} not found` };
  }

  const sourceHandle = sourceNode.outputs[sourceHandleName];
  const targetHandle = targetNode.inputs[targetHandleName];

  if (!areDataTypesCompatible(sourceHandle.dataType, targetHandle.dataType)) {
    return {
      valid: false,
      error: `Incompatible types: ${sourceHandle.dataType} → ${targetHandle.dataType}`
    };
  }

  return { valid: true };
}

// Batch validate multiple connections
export function validateConnections(
  arrows: Arrow[],
  nodes: Map<string, DiagramNode>
): {
  valid: Arrow[];
  invalid: Array<{ arrow: Arrow; error: string }>;
} {
  const valid: Arrow[] = [];
  const invalid: Array<{ arrow: Arrow; error: string }> = [];

  for (const arrow of arrows) {
    const result = validateConnection(arrow, nodes);
    if (result.valid) {
      valid.push(arrow);
    } else {
      invalid.push({ arrow, error: result.error! });
    }
  }

  return { valid, invalid };
}

// Find all valid target handles for a source handle
export function findValidTargets(
  sourceNodeId: string,
  sourceHandleName: string,
  nodes: Map<string, DiagramNode>
): Array<{ nodeId: string; handleName: string; handleId: HandleID }> {
  const sourceNode = nodes.get(sourceNodeId);
  if (!sourceNode) return [];

  const sourceHandle = sourceNode.outputs[sourceHandleName];
  if (!sourceHandle) return [];

  const validTargets: Array<{ nodeId: string; handleName: string; handleId: HandleID }> = [];

  for (const [nodeId, node] of nodes) {
    // Don't connect to self
    if (nodeId === sourceNodeId) continue;

    for (const [handleName, handle] of Object.entries(node.inputs)) {
      if (areDataTypesCompatible(sourceHandle.dataType, handle.dataType)) {
        validTargets.push({
          nodeId,
          handleName,
          handleId: handle.id
        });
      }
    }
  }

  return validTargets;
}

// Find all valid source handles for a target handle
export function findValidSources(
  targetNodeId: string,
  targetHandleName: string,
  nodes: Map<string, DiagramNode>
): Array<{ nodeId: string; handleName: string; handleId: HandleID }> {
  const targetNode = nodes.get(targetNodeId);
  if (!targetNode) return [];

  const targetHandle = targetNode.inputs[targetHandleName];
  if (!targetHandle) return [];

  const validSources: Array<{ nodeId: string; handleName: string; handleId: HandleID }> = [];

  for (const [nodeId, node] of nodes) {
    // Don't connect to self
    if (nodeId === targetNodeId) continue;

    for (const [handleName, handle] of Object.entries(node.outputs)) {
      if (areDataTypesCompatible(handle.dataType, targetHandle.dataType)) {
        validSources.push({
          nodeId,
          handleName,
          handleId: handle.id
        });
      }
    }
  }

  return validSources;
}