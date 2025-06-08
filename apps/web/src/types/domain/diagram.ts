import { NodeID, HandleID, ArrowID, PersonID, ApiKeyID } from '../branded';
import { DomainNode } from './node';
import { DomainArrow } from './arrow';
import { DomainHandle } from './handle';
import { DomainPerson } from './person';
import { DomainApiKey } from './api-key';

/**
 * Pure domain diagram - the complete workflow representation
 * Uses separated handle storage for better performance and flexibility
 */
export interface DomainDiagram {
  nodes: Record<NodeID, DomainNode>;
  handles: Record<HandleID, DomainHandle>;
  arrows: Record<ArrowID, DomainArrow>;
  persons: Record<PersonID, DomainPerson>;
  apiKeys: Record<ApiKeyID, DomainApiKey>;
  metadata?: DiagramMetadata;
}

/**
 * Diagram metadata
 */
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

/**
 * Diagram validation result
 */
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

/**
 * Type guard for domain diagram
 */
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

/**
 * Create an empty diagram
 */
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

/**
 * Get all handles for a specific node
 */
export function getNodeHandles(
  diagram: DomainDiagram,
  nodeId: NodeID
): DomainHandle[] {
  return Object.values(diagram.handles).filter(
    handle => handle.nodeId === nodeId
  );
}

/**
 * Get all arrows connected to a node
 */
export function getNodeConnections(
  diagram: DomainDiagram,
  nodeId: NodeID
): { incoming: DomainArrow[]; outgoing: DomainArrow[] } {
  const incoming: DomainArrow[] = [];
  const outgoing: DomainArrow[] = [];

  for (const arrow of Object.values(diagram.arrows)) {
    const [sourceNodeId] = arrow.source.split(':');
    const [targetNodeId] = arrow.target.split(':');

    if (targetNodeId === nodeId) {
      incoming.push(arrow);
    }
    if (sourceNodeId === nodeId) {
      outgoing.push(arrow);
    }
  }

  return { incoming, outgoing };
}

export interface ConversationMessage {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  personId: PersonID;
  content: string;
  timestamp?: string;
  tokenCount?: number;
  nodeLabel?: string;
}
