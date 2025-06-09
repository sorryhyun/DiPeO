import type React from 'react';

// Re-export ReactFlow types for backward compatibility
export type { Connection, Edge, ReactFlowInstance } from '@xyflow/react';

// ArrowData type for backward compatibility
export type ArrowData = {
  label?: string;
  style?: React.CSSProperties;
};

