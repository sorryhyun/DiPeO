// types/index.ts - Re-export all types for backward compatibility

// Re-export all types from separate modules
export * from './primitives';
export * from './api';
export * from './diagram';
export * from './runtime';
export * from './ui';
export * from './errors';
export * from './handles';
export * from './form';
export * from './validation';

// Additional exports for backward compatibility
export { type HandleConfig, type NodeConfigItem } from '../config/types';
export { NODE_CONFIGS } from '../config';

// Re-export commonly used ReactFlow types for convenience
export type { Connection, Edge, ReactFlowInstance } from '@xyflow/react';