// types/index.ts - Re-export all types for backward compatibility

// Re-export all types from separate modules
export * from './primitives';
export * from './api';
export * from './diagram';
export * from './runtime';
export * from './ui';
export * from './errors';
export * from './handles';
export * from './ui/form';
export * from './validation';

// New type system exports
export type { 
  Brand,
  NodeID,
  HandleID,
  ArrowID,
  PersonID,
  nodeId,
  handleId,
  arrowId,
  personId,
  isNodeId,
  isHandleId,
  isArrowId,
  isPersonId,
  parseHandleId
} from './branded';
export * from './direction';
// Export diagram-v2 types except DiagramNode to avoid conflict
export {
  type NodeV2,
  type HandleV2,
  type ArrowV2,
  type PersonV2,
  type DiagramV2,
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
// Export arrow types with aliases to avoid conflicts
export { 
  type TypedArrow,
  type HandleRef,
  type Arrow as TypedArrowType,
  isArrow,
  createHandleRef,
  areDataTypesCompatible
} from './arrow';
// export * from './node-base'; // Removed - using domain types
// Export node types from domain for backward compatibility
export {
  type DiagramNode as TypedDiagramNode,
  type StartNode,
  type ConditionNode,
  type PersonJobNode,
  type EndpointNode,
  type DBNode,
  type JobNode,
  type UserResponseNode,
  type NotionNode,
  type PersonBatchJobNode,
  isNodeOfType
} from './domain/node';

// Create type guard aliases for backward compatibility
import { isNodeOfType, DomainNode } from './domain/node';
import { NodeType } from './enums';

export const isStartNode = (node: DomainNode) => isNodeOfType(node, NodeType.Start);
export const isConditionNode = (node: DomainNode) => isNodeOfType(node, NodeType.Condition);
export const isPersonJobNode = (node: DomainNode) => isNodeOfType(node, NodeType.PersonJob);
export const isEndpointNode = (node: DomainNode) => isNodeOfType(node, NodeType.Endpoint);
export const isDBNode = (node: DomainNode) => isNodeOfType(node, NodeType.DB);
export const isJobNode = (node: DomainNode) => isNodeOfType(node, NodeType.Job);
export const isUserResponseNode = (node: DomainNode) => isNodeOfType(node, NodeType.UserResponse);
export const isNotionNode = (node: DomainNode) => isNodeOfType(node, NodeType.Notion);
export const isPersonBatchJobNode = (node: DomainNode) => isNodeOfType(node, NodeType.PersonBatchJob);

// Additional exports for backward compatibility
export { type HandleConfig, type NodeConfigItem } from '../config/types';
export { NODE_CONFIGS } from '../config';

// Re-export commonly used ReactFlow types for convenience
export type { Connection, Edge, ReactFlowInstance } from '@xyflow/react';