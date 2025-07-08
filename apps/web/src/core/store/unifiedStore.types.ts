import type { DomainArrow, DomainHandle, DomainNode, DomainPerson } from '@/core/types';
import type { DiagramSlice } from '@/features/diagram-editor/store/diagramSlice';
import type { ComputedSlice } from './slices/computedSlice';
import type { ExecutionSlice } from '@/features/execution-monitor/store/executionSlice';
import type { PersonSlice } from '@/features/person-management/store/personSlice';
import type { UISlice } from './slices/uiSlice';
import type { NodeID, ArrowID, PersonID, HandleID } from '@dipeo/domain-models';

// Re-export NodeState from executionSlice for backward compatibility
export type { NodeState } from '@/features/execution-monitor/store/executionSlice';

// Note: Export format types have been moved to diagramExporter.ts

// History types
export interface Snapshot {
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
  handles: Map<HandleID, DomainHandle>;
  timestamp: number;
}

interface Transaction {
  id: string;
  changes: unknown[];
  timestamp: number;
}

// Unified store interface extends all slices
export interface UnifiedStore extends 
  DiagramSlice,
  ComputedSlice,
  ExecutionSlice,
  PersonSlice,
  UISlice {
  // === Additional Core Data not in slices ===
  handles: Map<HandleID, DomainHandle>;
  handleIndex: Map<NodeID, DomainHandle[]>;  // Performance optimization: O(1) handle lookups by node
  
  // === History ===
  history: {
    undoStack: Snapshot[];
    redoStack: Snapshot[];
    currentTransaction: Transaction | null;
  };
  
  // === Additional Actions not in slices ===
  
  
  // History
  canUndo: boolean;
  canRedo: boolean;
  undo: () => void;
  redo: () => void;
  
  // Transactions
  transaction: <T>(fn: () => T) => T;
  
  // Utilities
  createSnapshot: () => Snapshot;
  restoreSnapshot: (snapshot: Snapshot) => void;
  clearAll: () => void;
  cleanupNodeHandles: (nodeId: NodeID) => void;
}
