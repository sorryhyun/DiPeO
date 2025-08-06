import type {
  NodeID,
  ArrowID,
  PersonID,
  HandleID,
  ExecutionID,
  DiagramID,
  DomainNode,
  DomainArrow,
  DomainPerson,
  DomainHandle,
  NodeType,
  Vec2,
  DiagramFormat,
} from '@dipeo/models';

import type { StoreExecutionState, StoreNodeState } from '@/infrastructure/converters';
import type { DiagramSlice } from './slices/diagram';
import type { ExecutionSlice } from './slices/execution';
import type { PersonSlice } from './slices/person';
import type { UISlice } from './slices/ui';
import type { ComputedSlice } from './slices/computedSlice';

export type {
  NodeID,
  ArrowID,
  PersonID,
  HandleID,
  ExecutionID,
  DiagramID,
  StoreExecutionState as ExecutionState,
  StoreNodeState as NodeExecutionState,
};

// ===== Store Snapshot for History =====

export interface Snapshot {
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
  handles: Map<HandleID, DomainHandle>;
  timestamp: number;
}

// Alias for backward compatibility
export type StoreSnapshot = Snapshot;

export interface Transaction {
  id: string;
  changes: unknown[];
  timestamp: number;
}

// ===== Action Patterns =====

export interface AsyncAction<T = void> {
  type: string;
  execute: () => Promise<T>;
  onSuccess?: (result: T) => void;
  onError?: (error: Error) => void;
}

export interface BatchAction<T> {
  items: T[];
  processor: (item: T) => void;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings?: string[];
}

// ===== Middleware Types =====

export interface MiddlewareContext {
  action: string;
  payload: unknown;
  timestamp: number;
  userId?: string;
}

export interface SideEffect {
  trigger: (context: MiddlewareContext) => boolean;
  execute: (context: MiddlewareContext) => Promise<void>;
}

// ===== Store Configuration =====

export interface StoreConfig {
  enableDevtools: boolean;
  enableLogging: boolean;
  enablePersistence: boolean;
  persistenceKey?: string;
  middleware?: StoreMiddleware[];
}

export interface StoreMiddleware {
  name: string;
  before?: (context: MiddlewareContext) => void;
  after?: (context: MiddlewareContext) => void;
}

// ===== Selector Types =====

export type Selector<T> = (state: UnifiedStore) => T;
export type ParameterizedSelector<P, T> = (params: P) => Selector<T>;

// ===== Unified Store Interface (Flattened) =====
// Uses composition to extend all slice interfaces

export interface UnifiedStore extends 
  DiagramSlice,
  ExecutionSlice,
  PersonSlice,
  UISlice,
  ComputedSlice {
  // === Additional Core Data ===
  handles: Map<HandleID, DomainHandle>;
  handleIndex: Map<NodeID, DomainHandle[]>;
  
  // === History ===
  history: {
    undoStack: StoreSnapshot[];
    redoStack: StoreSnapshot[];
    currentTransaction: Transaction | null;
  };
  
  // === History Actions ===
  canUndo: boolean;
  canRedo: boolean;
  undo: () => void;
  redo: () => void;
  
  // === Transaction Support ===
  transaction: <T>(fn: () => T) => T;
  
  // === Utilities ===
  createSnapshot: () => StoreSnapshot;
  restoreSnapshot: (snapshot: StoreSnapshot) => void;
  clearAll: () => void;
  cleanupNodeHandles: (nodeId: NodeID) => void;
}