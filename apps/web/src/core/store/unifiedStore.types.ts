import type { DomainApiKey, DomainArrow, DomainHandle, DomainNode, DomainPerson } from '@/core/types';
import type { DiagramSlice } from '@/features/diagram-editor/store/diagramSlice';
import type { ComputedSlice } from './slices/computedSlice';
import type { ExecutionSlice, NodeState } from '@/features/execution-monitor/store/executionSlice';
import type { PersonSlice } from '@/features/person-management/store/personSlice';
import type { UISlice } from './slices/uiSlice';
import type { NodeID, ArrowID, PersonID, HandleID, ApiKeyID, NodeType } from '@dipeo/domain-models';

// Re-export NodeState from executionSlice for backward compatibility
export type { NodeState } from '@/features/execution-monitor/store/executionSlice';

// Note: Export format types have been moved to diagramExporter.ts

// History types
export interface Snapshot {
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
  handles: Map<HandleID, DomainHandle>;
  apiKeys: Map<ApiKeyID, DomainApiKey>;
  timestamp: number;
}

interface Transaction {
  id: string;
  changes: any[];
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
  apiKeys: Map<ApiKeyID, DomainApiKey>;
  
  // === History ===
  history: {
    undoStack: Snapshot[];
    redoStack: Snapshot[];
    currentTransaction: Transaction | null;
  };
  
  // === Additional Actions not in slices ===
  
  // API Key operations
  addApiKey: (name: string, service: string) => ApiKeyID;
  updateApiKey: (id: ApiKeyID, updates: Partial<DomainApiKey>) => void;
  deleteApiKey: (id: ApiKeyID) => void;
  
  
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
  
  // Legacy array selectors (use nodesArray, arrowsArray, personsArray from slices instead)
  getNodes: () => DomainNode[];
  getArrows: () => DomainArrow[];
  getPersons: () => DomainPerson[];
  
}
