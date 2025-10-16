import { UnifiedStore } from '../types';
import type { StateCreator } from 'zustand';

/**
 * Standardized action patterns for consistent store operations
 */

// ===== CRUD Pattern =====

export interface CRUDActions<T, ID> {
  create: (data: Omit<T, 'id'>) => ID;
  read: (id: ID) => T | undefined;
  update: (id: ID, updates: Partial<T>) => void;
  delete: (id: ID) => void;
  list: () => T[];
}

export function createCRUDActions<T extends { id: ID }, ID>(
  entityName: string,
  mapKey: keyof UnifiedStore
): CRUDActions<T, ID> {
  return {
    create: (data) => {
      // Implementation provided by slice
      throw new Error(`${entityName}.create not implemented`);
    },
    read: (id) => {
      // Implementation provided by slice
      throw new Error(`${entityName}.read not implemented`);
    },
    update: (id, updates) => {
      // Implementation provided by slice
      throw new Error(`${entityName}.update not implemented`);
    },
    delete: (id) => {
      // Implementation provided by slice
      throw new Error(`${entityName}.delete not implemented`);
    },
    list: () => {
      // Implementation provided by slice
      throw new Error(`${entityName}.list not implemented`);
    },
  };
}

// ===== Async Action Pattern =====

export interface AsyncActionConfig<T> {
  name: string;
  execute: () => Promise<T>;
  onStart?: () => void;
  onSuccess?: (result: T) => void;
  onError?: (error: Error) => void;
  onFinally?: () => void;
}

export function createAsyncAction<T>(
  config: AsyncActionConfig<T>
) {
  return async () => {
    const { execute, onStart, onSuccess, onError, onFinally } = config;

    try {
      onStart?.();
      const result = await execute();
      onSuccess?.(result);
      return result;
    } catch (error) {
      onError?.(error as Error);
      throw error;
    } finally {
      onFinally?.();
    }
  };
}

// ===== Batch Action Pattern =====

export interface BatchActionConfig<T> {
  items: T[];
  processor: (item: T) => void | Promise<void>;
  onProgress?: (processed: number, total: number) => void;
  parallel?: boolean;
}

export async function executeBatchAction<T>(
  config: BatchActionConfig<T>
): Promise<void> {
  const { items, processor, onProgress, parallel = false } = config;

  if (parallel) {
    await Promise.all(
      items.map(async (item, index) => {
        await processor(item);
        onProgress?.(index + 1, items.length);
      })
    );
  } else {
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item !== undefined) {
        await processor(item);
      }
      onProgress?.(i + 1, items.length);
    }
  }
}

// ===== Optimistic Update Pattern =====

export interface OptimisticUpdateConfig<T> {
  optimisticUpdate: () => void;
  serverUpdate: () => Promise<T>;
  rollback: () => void;
  commit: (result: T) => void;
}

export async function executeOptimisticUpdate<T>(
  config: OptimisticUpdateConfig<T>
): Promise<T> {
  const { optimisticUpdate, serverUpdate, rollback, commit } = config;

  // Apply optimistic update
  optimisticUpdate();

  try {
    // Perform server update
    const result = await serverUpdate();
    // Commit the result
    commit(result);
    return result;
  } catch (error) {
    // Rollback on error
    rollback();
    throw error;
  }
}

// ===== Transaction Pattern =====

export interface TransactionConfig {
  id?: string;
  operations: (() => void)[];
  beforeCommit?: () => void;
  afterCommit?: () => void;
  onRollback?: () => void;
}

export function createTransaction(
  get: () => UnifiedStore,
  set: (partial: Partial<UnifiedStore> | ((state: UnifiedStore) => Partial<UnifiedStore> | void), replace?: boolean) => void
) {
  return (config: TransactionConfig) => {
    const { operations, beforeCommit, afterCommit, onRollback } = config;
    const transactionId = config.id || crypto.randomUUID();

    // Create snapshot before transaction
    const snapshot = get().history.undoStack[get().history.undoStack.length - 1];

    try {
      // Mark transaction start
      set((state: UnifiedStore) => ({
        history: {
          ...state.history,
          currentTransaction: {
            id: transactionId,
            changes: [],
            timestamp: Date.now(),
          }
        }
      }));

      beforeCommit?.();

      // Execute all operations
      operations.forEach(op => op());

      // Commit transaction
      set((state: UnifiedStore) => {
        if (state.history.currentTransaction?.id === transactionId && snapshot) {
          return {
            history: {
              ...state.history,
              undoStack: [...state.history.undoStack, {
                ...snapshot,
                timestamp: Date.now(),
              }],
              currentTransaction: null
            }
          };
        }
        return {};
      });

      afterCommit?.();
      return true;
    } catch (error) {
      // Rollback on error
      onRollback?.();

      // Restore from snapshot
      if (snapshot) {
        set((state: any) => {
          Object.assign(state, snapshot);
          state.history.currentTransaction = null;
        });
      }

      throw error;
    }
  };
}

// ===== Validation Pattern =====

export interface ValidationConfig<T> {
  data: T;
  validators: Array<(data: T) => string | null>;
}

export function validateWithPattern<T>(
  config: ValidationConfig<T>
): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];

  for (const validator of config.validators) {
    const error = validator(config.data);
    if (error) {
      errors.push(error);
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

// ===== Subscription Pattern =====

export interface SubscriptionConfig<T> {
  selector: (state: UnifiedStore) => T;
  onChange: (value: T, previousValue: T) => void;
  equalityFn?: (a: T, b: T) => boolean;
}

export function createSubscription<T>(
  subscribe: (listener: (state: UnifiedStore) => void) => () => void,
  getState: () => UnifiedStore
) {
  return (config: SubscriptionConfig<T>): (() => void) => {
    const { selector, onChange, equalityFn = Object.is } = config;

    let previousValue = selector(getState());

    return subscribe((state) => {
      const currentValue = selector(state);
      if (!equalityFn(currentValue, previousValue)) {
        onChange(currentValue, previousValue);
        previousValue = currentValue;
      }
    });
  };
}

// ===== Computed Values Pattern =====

export interface ComputedConfig<T> {
  dependencies: Array<(state: UnifiedStore) => unknown>;
  compute: (...deps: unknown[]) => T;
  memoize?: boolean;
}

export function createComputed<T>(
  config: ComputedConfig<T>
) {
  const { dependencies, compute, memoize = true } = config;

  let cachedDeps: unknown[] | null = null;
  let cachedResult: T | null = null;

  return (state: UnifiedStore): T => {
    const currentDeps = dependencies.map(dep => dep(state));

    if (memoize && cachedDeps && arraysEqual(currentDeps, cachedDeps)) {
      return cachedResult!;
    }

    const result = compute(...currentDeps);

    if (memoize) {
      cachedDeps = currentDeps;
      cachedResult = result;
    }

    return result;
  };
}

// Helper function
function arraysEqual(a: unknown[], b: unknown[]): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}
