import { NodeID, HandleID, ArrowID, PersonID, ApiKeyID } from '../branded';
import { DomainNode } from './node';
import { DomainArrow } from './arrow';
import { DomainHandle, parseHandleId } from './handle';
import { DomainPerson } from './person';
import { DomainApiKey } from './api-key';

export interface DomainDiagram {
  nodes: Record<NodeID, DomainNode>;
  handles: Record<HandleID, DomainHandle>;
  arrows: Record<ArrowID, DomainArrow>;
  persons: Record<PersonID, DomainPerson>;
  apiKeys: Record<ApiKeyID, DomainApiKey>;
  metadata?: DiagramMetadata;
}

export interface DiagramMetadata {
  id?: string;
  name?: string;
  description?: string;
  version: string;
  created: string;
  modified: string;
  author?: string;
  tags?: string[];
}

export interface DiagramValidation {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  type: 'missing_node' | 'missing_handle' | 'invalid_connection' | 'cycle_detected' | 'other';
  message: string;
  nodeId?: NodeID;
  handleId?: HandleID;
  arrowId?: ArrowID;
}

export interface ValidationWarning {
  type: 'unused_node' | 'unused_handle' | 'missing_person' | 'other';
  message: string;
  nodeId?: NodeID;
  handleId?: HandleID;
}

export function isDomainDiagram(obj: unknown): obj is DomainDiagram {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'nodes' in obj &&
    'handles' in obj &&
    'arrows' in obj &&
    'persons' in obj &&
    'apiKeys' in obj
  );
}

export function createEmptyDiagram(): DomainDiagram {
  return {
    nodes: {},
    handles: {},
    arrows: {},
    persons: {},
    apiKeys: {},
    metadata: {
      version: '2.0.0',
      created: new Date().toISOString(),
      modified: new Date().toISOString()
    }
  };
}

export function getNodeHandles(
  diagram: DomainDiagram,
  nodeId: NodeID
): DomainHandle[] {
  return Object.values(diagram.handles).filter(
    handle => handle.nodeId === nodeId
  );
}

export function getHandleById(diagram: DomainDiagram, handleId: HandleID): DomainHandle | undefined {
  return diagram.handles[handleId];
}

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

export function getNodeConnections(
  diagram: DomainDiagram,
  nodeId: NodeID
): { incoming: DomainArrow[]; outgoing: DomainArrow[] } {
  const incoming: DomainArrow[] = [];
  const outgoing: DomainArrow[] = [];

  // We still need to check direction separately, so can't use connectsToNode here
  for (const arrow of Object.values(diagram.arrows)) {
    const source = parseHandleId(arrow.source);
    const target = parseHandleId(arrow.target);

    if (target.nodeId === nodeId) {
      incoming.push(arrow);
    }
    if (source.nodeId === nodeId) {
      outgoing.push(arrow);
    }
  }

  return { incoming, outgoing };
}

