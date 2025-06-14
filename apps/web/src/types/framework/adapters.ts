import { Node as RFNode, Edge as RFEdge, Connection } from '@xyflow/react';
import { 
  DomainNode, 
  DomainArrow, 
  DomainHandle, 
  DomainDiagram,
  getNodeHandles,
  areHandlesCompatible,
  parseHandleId
} from '../domain';
import { NodeID, ArrowID, HandleID, handleId } from '../branded';
import { DiPeoNode, DiPeoEdge, ValidatedConnection } from './reactUtils';
import { Vec2, Rect, NodeKind, generateId } from '../primitives';


/**
 * Convert domain node to React node
 */
export function nodeToReact(node: DomainNode, handles: DomainHandle[]): DiPeoNode {
  // Separate handles by direction
  const inputs = handles
    .filter(h => h.direction === 'input')
    .reduce((acc, h) => ({ ...acc, [h.label]: h }), {});
  
  const outputs = handles
    .filter(h => h.direction === 'output')
    .reduce((acc, h) => ({ ...acc, [h.label]: h }), {});

  return {
    id: node.id,
    type: node.type,
    position: node.position,
    data: {
      ...node.data,
      label: (node.data as any).label || '',
      inputs,
      outputs
    },
    // Add default React Flow properties required for proper node initialization
    draggable: true,
    selectable: true,
    connectable: true,
    focusable: true,
    deletable: true
  };
}

/**
 * Convert domain arrow to React edge
 */
export function arrowToReact(arrow: DomainArrow): DiPeoEdge {
  const { nodeId: sourceNode, handleLabel: sourceHandle } = parseHandleId(arrow.source);
  const { nodeId: targetNode, handleLabel: targetHandle } = parseHandleId(arrow.target);
  
  return {
    id: arrow.id,
    type: 'customArrow',
    source: sourceNode,
    target: targetNode,
    sourceHandle,
    targetHandle,
    data: arrow.data || {}
  };
}

/**
 * Convert full domain diagram to React elements
 */
export function diagramToReact(diagram: DomainDiagram): {
  nodes: DiPeoNode[];
  edges: DiPeoEdge[];
} {
  const nodes = Object.values(diagram.nodes).map(node => {
    const handles = getNodeHandles(diagram, node.id);
    return nodeToReact(node, handles);
  });

  const edges = Object.values(diagram.arrows).map(arrow => arrowToReact(arrow));

  return { nodes, edges };
}


// React to Domain Conversions

export function reactToNode(rfNode: RFNode): DomainNode {
  const { inputs, outputs, ...nodeData } = rfNode.data || {};
  return {
    id: rfNode.id as NodeID,
    type: (rfNode.type as NodeKind) || 'start',
    position: rfNode.position,
    data: nodeData as any
  };
}

export function reactToArrow(rfEdge: RFEdge): DomainArrow {
  const sourceHandle = handleId(
    rfEdge.source as NodeID, 
    rfEdge.sourceHandle || 'default'
  );
  const targetHandle = handleId(
    rfEdge.target as NodeID,
    rfEdge.targetHandle || 'default'
  );

  return {
    id: rfEdge.id as ArrowID,
    source: sourceHandle,
    target: targetHandle,
    data: rfEdge.data || {}
  };
}

export function connectionToArrow(connection: Connection): DomainArrow | null {
  if (!connection.source || !connection.target) {
    return null;
  }

  const sourceHandle = handleId(
    connection.source as NodeID,
    connection.sourceHandle || 'default'
  );
  const targetHandle = handleId(
    connection.target as NodeID,
    connection.targetHandle || 'default'
  );

  return {
    id: generateId() as ArrowID,
    source: sourceHandle,
    target: targetHandle
  };
}

// Validation and Utilities

export function validateConnection(
  connection: Connection,
  diagram: DomainDiagram
): ValidatedConnection {
  const validated: ValidatedConnection = { ...connection };

  if (!connection.source || !connection.target) {
    validated.isValid = false;
    validated.validationMessage = 'Missing source or target';
    return validated;
  }

  const sourceHandleId = handleId(
    connection.source as NodeID,
    connection.sourceHandle || 'default'
  );
  const targetHandleId = handleId(
    connection.target as NodeID,
    connection.targetHandle || 'default'
  );

  // Find the actual handles
  const sourceHandle = diagram.handles[sourceHandleId];
  const targetHandle = diagram.handles[targetHandleId];

  if (!sourceHandle || !targetHandle) {
    validated.isValid = false;
    validated.validationMessage = 'Handle not found';
    return validated;
  }

  // Check compatibility
  if (!areHandlesCompatible(sourceHandle, targetHandle)) {
    validated.isValid = false;
    validated.validationMessage = 'Incompatible handle types';
    return validated;
  }

  validated.isValid = true;
  return validated;
}


export function normalizePosition(position: Partial<Vec2> | undefined): Vec2 {
  return {
    x: position?.x ?? 0,
    y: position?.y ?? 0
  };
}

/**
 * Calculate bounding box of all nodes in a diagram
 */
export function calculateDiagramBounds(nodes: DomainNode[]): Rect {
  if (nodes.length === 0) {
    return { x: 0, y: 0, width: 0, height: 0 };
  }

  const nodeWidth = 150;
  const nodeHeight = 50;

  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  nodes.forEach(node => {
    const x = node.position.x;
    const y = node.position.y;
    
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x + nodeWidth);
    maxY = Math.max(maxY, y + nodeHeight);
  });

  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY
  };
}