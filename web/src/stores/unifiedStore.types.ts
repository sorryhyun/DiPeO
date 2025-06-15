import type {
  NodeID,  ArrowID,  PersonID,  HandleID,  ApiKeyID,
  DomainNode,  DomainArrow,  DomainPerson,  DomainHandle,  DomainApiKey,
  NodeKind,  Vec2,  LlmService,} from '@/types';
import type { DiagramSlice } from './slices/diagramSlice';
import type { ComputedSlice } from './slices/computedSlice';
import type { ExecutionSlice, NodeState } from './slices/executionSlice';
import type { PersonSlice } from './slices/personSlice';
import type { UISlice } from './slices/uiSlice';
import { DiagramFormat } from '@/__generated__/graphql';

// Re-export NodeState from executionSlice for backward compatibility
export type { NodeState } from './slices/executionSlice';

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
  
  // Export/Import operations (deprecated - use GraphQL operations)
  exportDiagram: () => any; // Deprecated - use useFileOperations hook
  exportAsYAML: () => string; // Deprecated - use useFileOperations hook
  importDiagram: (data: any, format?: DiagramFormat) => void; // Deprecated - use useFileOperations hook
  validateExportData: (data: unknown) => { valid: boolean; errors: string[] }; // Deprecated - validation handled by backend
}
