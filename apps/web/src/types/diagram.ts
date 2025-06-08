import type { NodeID, HandleID, ArrowID, PersonID, ApiKeyID } from './branded';
import type { Direction } from './direction';
import type { DataType } from './handles';
import type { DomainApiKey } from './domain/api-key';
import {DomainDiagram, DomainHandle, DomainNode} from "@/types/domain";

export type NodeWithHandles = DomainNode & {
  handles: DomainHandle[];
};

// Utility function to get handles for a node
export function getNodeHandles(diagram: DomainDiagram, nodeId: NodeID): DomainHandle[] {
  return Object.values(diagram.handles).filter(h => h.nodeId === nodeId);
}

// Utility function to get a handle by its ID
export function getHandleById(diagram: DomainDiagram, handleId: HandleID): DomainHandle | undefined {
  return diagram.handles[handleId];
}

// Utility function to get connected handles
export function getConnectedHandles(diagram: DomainDiagram, handleId: HandleID): DomainHandle[] {
  const connectedHandleIds = new Set<HandleID>();
  
  Object.values(diagram.arrows).forEach(arrow => {
    if (arrow.source === handleId) {
      connectedHandleIds.add(arrow.target);
    } else if (arrow.target === handleId) {
      connectedHandleIds.add(arrow.source);
    }
  });
  
  return Array.from(connectedHandleIds)
    .map(id => diagram.handles[id])
    .filter(Boolean) as DomainHandle[];
}

// Re-export DiagramNode from domain for backward compatibility
export type { DiagramNode } from './domain/node';