/**
 * Factory for creating store operation hooks
 * Reduces code duplication across entity operation hooks
 */

import { useState, useCallback, useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { toast } from 'sonner';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';
import type { UnifiedStore } from '@/infrastructure/store/types';

// Base configuration for operation hooks
export interface OperationHookConfig<TEntity, TCreateArgs extends unknown[] = unknown[]> {
  // Entity configuration
  entityName: string; // Human-readable name for toasts
  entityNamePlural?: string; // Plural form (defaults to entityName + 's')

  // Store selectors
  selectCollection: (state: UnifiedStore) => Map<string, TEntity>;
  selectAddAction?: (state: UnifiedStore) => (...args: TCreateArgs) => string;
  selectUpdateAction?: (state: UnifiedStore) => (id: string, updates: Partial<TEntity>) => void;
  selectDeleteAction?: (state: UnifiedStore) => (id: string) => void;
  selectClearAction?: (state: UnifiedStore) => () => void;

  // Additional selectors for related data
  selectRelated?: (state: UnifiedStore) => unknown;

  // Lifecycle hooks
  beforeAdd?: (...args: TCreateArgs) => TCreateArgs | Promise<TCreateArgs>;
  afterAdd?: (id: string, ...args: TCreateArgs) => void | Promise<void>;
  beforeUpdate?: (id: string, updates: Partial<TEntity>) => Partial<TEntity> | Promise<Partial<TEntity>>;
  afterUpdate?: (id: string, updates: Partial<TEntity>) => void | Promise<void>;
  beforeDelete?: (id: string) => boolean | Promise<boolean>;
  afterDelete?: (id: string) => void | Promise<void>;

  // Validation
  validateAdd?: (...args: TCreateArgs) => { isValid: boolean; errors: string[] };
  validateUpdate?: (id: string, updates: Partial<TEntity>) => { isValid: boolean; errors: string[] };

  // Custom messages
  messages?: {
    addSuccess?: string | ((...args: TCreateArgs) => string);
    updateSuccess?: string | ((id: string) => string);
    deleteSuccess?: string | ((id: string) => string);
    addError?: string;
    updateError?: string;
    deleteError?: string;
    validationError?: string;
  };

  // Options
  options?: {
    useTransaction?: boolean; // Wrap operations in store transaction
    showToasts?: boolean; // Show toast notifications
    trackDirty?: boolean; // Track if collection has been modified
  };
}

// Return type for operation hooks
export interface OperationHookReturn<TEntity, TCreateArgs extends unknown[] = unknown[]> {
  // Collection state
  items: TEntity[];
  itemsMap: Map<string, TEntity>;
  count: number;

  // Operation state
  isProcessing: boolean;
  errors: Record<string, string>;
  isDirty: boolean;

  // CRUD operations
  add: (...args: TCreateArgs) => Promise<string | null>;
  update: (id: string, updates: Partial<TEntity>) => Promise<boolean>;
  delete: (id: string) => Promise<boolean>;
  clear?: () => Promise<void>;

  // Utilities
  getById: (id: string) => TEntity | undefined;
  exists: (id: string) => boolean;
  validate: (operation: 'add' | 'update', ...args: unknown[]) => { isValid: boolean; errors: string[] };
  clearErrors: () => void;
  setDirty: (dirty: boolean) => void;
}

/**
 * Creates a store operation hook with standardized CRUD operations
 */
export function createStoreOperationHook<TEntity, TCreateArgs extends unknown[] = unknown[]>(
  config: OperationHookConfig<TEntity, TCreateArgs>
): () => OperationHookReturn<TEntity, TCreateArgs> {
  const {
    entityName,
    entityNamePlural = `${entityName}s`,
    options = {
      useTransaction: true,
      showToasts: true,
      trackDirty: true
    }
  } = config;

  return function useOperationHook(): OperationHookReturn<TEntity, TCreateArgs> {
    // Local state
    const [isProcessing, setIsProcessing] = useState(false);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [isDirty, setIsDirty] = useState(false);

    // Store state with proper memoization
    const storeState = useUnifiedStore(useShallow((state) => ({
      collection: config.selectCollection(state),
      addAction: config.selectAddAction?.(state),
      updateAction: config.selectUpdateAction?.(state),
      deleteAction: config.selectDeleteAction?.(state),
      clearAction: config.selectClearAction?.(state),
      transaction: state.transaction,
      related: config.selectRelated?.(state)
    })));

    // Convert collection to array - memoized by size
    const items = useMemo(
      () => Array.from(storeState.collection.values()),
      [storeState.collection.size]
    );

    // Helper to get message
    const getMessage = (
      messageKey: keyof NonNullable<typeof config.messages>,
      ...args: unknown[]
    ): string => {
      const message = config.messages?.[messageKey];
      if (typeof message === 'function') {
        return (message as (...args: unknown[]) => string)(...args);
      }
      return message || `${entityName} operation ${messageKey.replace(/Success|Error/, '')}`;
    };

    // Validation helper
    const validate = useCallback((
      operation: 'add' | 'update',
      ...args: unknown[]
    ): { isValid: boolean; errors: string[] } => {
      if (operation === 'add' && config.validateAdd) {
        // Apply the spread using apply to avoid TypeScript issues
        return config.validateAdd.apply(null, args as TCreateArgs);
      }
      if (operation === 'update' && config.validateUpdate) {
        return config.validateUpdate(args[0] as string, args[1] as Partial<TEntity>);
      }
      return { isValid: true, errors: [] };
    }, []);

    // Add operation
    const add = useCallback(async (...args: TCreateArgs): Promise<string | null> => {
      if (!storeState.addAction) {
        console.error(`Add action not configured for ${entityName}`);
        return null;
      }

      setIsProcessing(true);
      setErrors({});

      try {
        // Validation
        const validation = validate('add', ...args);
        if (!validation.isValid) {
          const errorMsg = validation.errors[0] || config.messages?.validationError || 'Validation failed';
          setErrors({ add: errorMsg });
          if (options.showToasts) toast.error(errorMsg);
          return null;
        }

        // Before hook
        let processedArgs = args;
        if (config.beforeAdd) {
          processedArgs = await config.beforeAdd(...args);
        }

        // Execute operation
        let id: string;
        if (options.useTransaction && storeState.transaction) {
          storeState.transaction(() => {
            id = storeState.addAction!(...processedArgs);
          });
        } else {
          id = storeState.addAction!(...processedArgs);
        }

        // After hook
        if (config.afterAdd) {
          await config.afterAdd(id!, ...processedArgs);
        }

        // Update state
        if (options.trackDirty) setIsDirty(true);
        if (options.showToasts) {
          toast.success(getMessage('addSuccess', ...processedArgs));
        }

        return id!;
      } catch (error) {
        const errorMsg = getMessage('addError');
        setErrors({ add: errorMsg });
        if (options.showToasts) toast.error(errorMsg);
        console.error(`Failed to add ${entityName}:`, error);
        return null;
      } finally {
        setIsProcessing(false);
      }
    }, [storeState, validate, options, entityName]);

    // Update operation
    const update = useCallback(async (
      id: string,
      updates: Partial<TEntity>
    ): Promise<boolean> => {
      if (!storeState.updateAction) {
        console.error(`Update action not configured for ${entityName}`);
        return false;
      }

      setIsProcessing(true);
      setErrors({});

      try {
        // Validation
        const validation = validate('update', id, updates);
        if (!validation.isValid) {
          const errorMsg = validation.errors[0] || config.messages?.validationError || 'Validation failed';
          setErrors({ update: errorMsg });
          if (options.showToasts) toast.error(errorMsg);
          return false;
        }

        // Before hook
        let processedUpdates = updates;
        if (config.beforeUpdate) {
          processedUpdates = await config.beforeUpdate(id, updates);
        }

        // Execute operation
        if (options.useTransaction && storeState.transaction) {
          storeState.transaction(() => {
            storeState.updateAction!(id, processedUpdates);
          });
        } else {
          storeState.updateAction(id, processedUpdates);
        }

        // After hook
        if (config.afterUpdate) {
          await config.afterUpdate(id, processedUpdates);
        }

        // Update state
        if (options.trackDirty) setIsDirty(true);
        if (options.showToasts) {
          toast.success(getMessage('updateSuccess', id));
        }

        return true;
      } catch (error) {
        const errorMsg = getMessage('updateError');
        setErrors({ update: errorMsg });
        if (options.showToasts) toast.error(errorMsg);
        console.error(`Failed to update ${entityName}:`, error);
        return false;
      } finally {
        setIsProcessing(false);
      }
    }, [storeState, validate, options, entityName]);

    // Delete operation
    const deleteItem = useCallback(async (id: string): Promise<boolean> => {
      if (!storeState.deleteAction) {
        console.error(`Delete action not configured for ${entityName}`);
        return false;
      }

      setIsProcessing(true);
      setErrors({});

      try {
        // Before hook
        if (config.beforeDelete) {
          const canDelete = await config.beforeDelete(id);
          if (!canDelete) {
            return false;
          }
        }

        // Execute operation
        if (options.useTransaction && storeState.transaction) {
          storeState.transaction(() => {
            storeState.deleteAction!(id);
          });
        } else {
          storeState.deleteAction(id);
        }

        // After hook
        if (config.afterDelete) {
          await config.afterDelete(id);
        }

        // Update state
        if (options.trackDirty) setIsDirty(true);
        if (options.showToasts) {
          toast.success(getMessage('deleteSuccess', id));
        }

        return true;
      } catch (error) {
        const errorMsg = getMessage('deleteError');
        setErrors({ delete: errorMsg });
        if (options.showToasts) toast.error(errorMsg);
        console.error(`Failed to delete ${entityName}:`, error);
        return false;
      } finally {
        setIsProcessing(false);
      }
    }, [storeState, options, entityName]);

    // Clear operation
    const clear = useCallback(async (): Promise<void> => {
      if (!storeState.clearAction) {
        return;
      }

      setIsProcessing(true);
      try {
        if (options.useTransaction && storeState.transaction) {
          storeState.transaction(() => {
            storeState.clearAction!();
          });
        } else {
          storeState.clearAction();
        }

        if (options.trackDirty) setIsDirty(true);
        if (options.showToasts) {
          toast.success(`All ${entityNamePlural} cleared`);
        }
      } finally {
        setIsProcessing(false);
      }
    }, [storeState, options, entityNamePlural]);

    // Utility functions
    const getById = useCallback((id: string): TEntity | undefined => {
      return storeState.collection.get(id);
    }, [storeState.collection]);

    const exists = useCallback((id: string): boolean => {
      return storeState.collection.has(id);
    }, [storeState.collection]);

    const clearErrors = useCallback(() => {
      setErrors({});
    }, []);

    return {
      // Collection state
      items,
      itemsMap: storeState.collection,
      count: storeState.collection.size,

      // Operation state
      isProcessing,
      errors,
      isDirty,

      // CRUD operations
      add,
      update,
      delete: deleteItem,
      ...(storeState.clearAction && { clear }),

      // Utilities
      getById,
      exists,
      validate,
      clearErrors,
      setDirty: setIsDirty
    };
  };
}
