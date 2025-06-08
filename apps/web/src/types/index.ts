// types/index.ts - Re-export all types for backward compatibility

// Re-export all types from separate modules
export * from './primitives';
export * from './api';
export * from './diagram';
export * from './runtime';
export * from './ui';
export * from './errors';
export * from './ui/form';
export * from './validation';

// Re-export from domain for backward compatibility
export * from './domain';
export * from './framework';

// New type system exports - types
export type { 
  Brand,
  NodeID,
  HandleID,
  ArrowID,
  PersonID,
  ApiKeyID
} from './branded';

// New type system exports - functions
export {
  nodeId,
  handleId,
  arrowId,
  personId,
  apiKeyId,
  isNodeId,
  isHandleId,
  isArrowId,
  isPersonId,
  isApiKeyId,
  parseHandleId
} from './branded';
// Export diagram utilities and types
export {
  type NodeWithHandles,
  getNodeHandles,
  getHandleById,
  getConnectedHandles,
  type DiagramNode as DiagramNodeV2
} from './diagram';
// Export enums explicitly to avoid conflicts
export { 
  NodeType, 
  DataType as DataTypeEnum, 
  ArrowType, 
  HandlePosition, 
  NodeExecutionState, 
  ConnectionMode 
} from './enums';
// export * from './node-specs'; // Removed - using domain types
// Node and arrow types are now in domain/
// Type guards are exported from domain

// Additional exports for backward compatibility
export { type HandleConfig, type NodeConfigItem } from '../config/types';
export { NODE_CONFIGS } from '../config';

// Re-export commonly used ReactFlow types for convenience
export type { Connection, Edge, ReactFlowInstance } from '@xyflow/react';

// Backward compatibility exports - old names to new domain types
export type { 
  DomainNode as Node,
  DomainArrow as Arrow,
  DomainPerson as Person,
  DomainApiKey as ApiKey,
  DomainDiagram as Diagram
} from './domain';

// NodeKind was replaced by NodeType enum
export { NodeType as NodeKind } from './enums';

// ArrowData type for backward compatibility
export type ArrowData = {
  label?: string;
  style?: React.CSSProperties;
};