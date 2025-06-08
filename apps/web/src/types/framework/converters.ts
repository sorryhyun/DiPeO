import { Connection } from 'reactflow';
import { DomainArrow, DomainDiagram, areHandlesCompatible } from '../domain';
import { ArrowID, HandleID, handleId, NodeID, generateId } from '../branded';
import { ValidatedConnection } from './react-flow';

/**
 * Convert React Flow connection to domain arrow
 */
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

/**
 * Validate a connection against the diagram
 */
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

  const sourceHandle = diagram.handles[sourceHandleId];
  const targetHandle = diagram.handles[targetHandleId];

  if (!sourceHandle) {
    validated.isValid = false;
    validated.validationMessage = `Source handle ${sourceHandleId} not found`;
    return validated;
  }

  if (!targetHandle) {
    validated.isValid = false;
    validated.validationMessage = `Target handle ${targetHandleId} not found`;
    return validated;
  }

  if (!areHandlesCompatible(sourceHandle, targetHandle)) {
    validated.isValid = false;
    validated.validationMessage = `Incompatible data types: ${sourceHandle.dataType} -> ${targetHandle.dataType}`;
    return validated;
  }

  // Check for duplicate connections
  const existingArrow = Object.values(diagram.arrows).find(
    arrow => arrow.source === sourceHandleId && arrow.target === targetHandleId
  );

  if (existingArrow) {
    validated.isValid = false;
    validated.validationMessage = 'Connection already exists';
    return validated;
  }

  // Check max connections on target
  if (targetHandle.maxConnections) {
    const incomingCount = Object.values(diagram.arrows).filter(
      arrow => arrow.target === targetHandleId
    ).length;

    if (incomingCount >= targetHandle.maxConnections) {
      validated.isValid = false;
      validated.validationMessage = `Target handle already has maximum connections (${targetHandle.maxConnections})`;
      return validated;
    }
  }

  validated.isValid = true;
  return validated;
}

/**
 * Convert node position for export
 */
export function normalizePosition(position: { x: number; y: number }): { x: number; y: number } {
  return {
    x: Math.round(position.x),
    y: Math.round(position.y)
  };
}

/**
 * Calculate diagram bounds
 */
export function calculateDiagramBounds(diagram: DomainDiagram): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
} {
  const positions = Object.values(diagram.nodes).map(n => n.position);
  
  if (positions.length === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0, width: 0, height: 0 };
  }

  const minX = Math.min(...positions.map(p => p.x));
  const minY = Math.min(...positions.map(p => p.y));
  const maxX = Math.max(...positions.map(p => p.x));
  const maxY = Math.max(...positions.map(p => p.y));

  return {
    minX,
    minY,
    maxX,
    maxY,
    width: maxX - minX,
    height: maxY - minY
  };
}