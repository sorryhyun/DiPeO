/**
 * Legacy type exports for backward compatibility
 * These exports maintain compatibility with older code that uses the previous type names.
 * New code should use the domain types directly.
 * 
 * @deprecated Use imports from specific modules instead of this file
 */

import type React from 'react';

// Re-export ReactFlow types for backward compatibility
export type { Connection, Edge, ReactFlowInstance } from '@xyflow/react';

// Backward compatibility type aliases - old names to new domain types
export type { 
  DomainNode as Node,
  DomainArrow as Arrow,
  DomainPerson as Person,
  DomainApiKey as ApiKey,
  DomainDiagram as Diagram
} from '../domain';

// ArrowData type for backward compatibility
export type ArrowData = {
  label?: string;
  style?: React.CSSProperties;
};

// Re-export commonly used handle utilities for backward compatibility
export {
  getNodeHandles,
  getHandleById,
  getConnectedHandles
} from '../domain/diagram';

// Note: These are maintained for backward compatibility only.
// New code should import directly from the appropriate modules:
// - Domain types from './domain'
// - Framework types from './framework'  
// - UI types from './ui'
// - Runtime types from './runtime'