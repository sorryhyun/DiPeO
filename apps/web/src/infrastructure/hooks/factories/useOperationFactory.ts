/**
 * Unified operation factory for creating consistent operation hooks
 * Supports both store and GraphQL operations with standardized patterns
 */

import { useState, useCallback, useMemo } from 'react';
import { DocumentNode, OperationVariables } from '@apollo/client';
import { createEntityQuery, createEntityMutation } from '@/lib/graphql/hooks/factory';
import { createStoreOperationHook, type OperationHookConfig } from './storeOpFactory';

/**
 * Unified operation type
 */
export type OperationType = 'store' | 'graphql';

/**
 * Base configuration shared by all operations
 */
export interface BaseOperationConfig {
  entityName: string;
  entityNamePlural?: string;
  messages?: {
    addSuccess?: string | ((...args: any[]) => string);
    updateSuccess?: string | ((id: string) => string);
    deleteSuccess?: string | ((id: string) => string);
    fetchSuccess?: string;
    addError?: string;
    updateError?: string;
    deleteError?: string;
    fetchError?: string;
    validationError?: string;
  };
  options?: {
    showToasts?: boolean;
    trackDirty?: boolean;
    optimisticResponse?: boolean;
  };
}

/**
 * Store-specific operation configuration
 */
export interface StoreOperationConfig<TEntity, TCreateArgs extends unknown[] = unknown[]>
  extends Omit<BaseOperationConfig, 'messages' | 'options'>, OperationHookConfig<TEntity, TCreateArgs> {
  type: 'store';
}

/**
 * GraphQL-specific operation configuration
 */
export interface GraphQLOperationConfig<_TData = any, _TVariables extends OperationVariables = OperationVariables>
  extends BaseOperationConfig {
  type: 'graphql';
  documents: {
    query?: DocumentNode;
    create?: DocumentNode;
    update?: DocumentNode;
    delete?: DocumentNode;
    list?: DocumentNode;
    subscription?: DocumentNode;
  };
  cacheStrategy?: 'cache-first' | 'cache-and-network' | 'network-only' | 'no-cache' | 'cache-only';
}

/**
 * Unified operation configuration
 */
export type UnifiedOperationConfig<TEntity = any, TCreateArgs extends unknown[] = unknown[]> =
  | StoreOperationConfig<TEntity, TCreateArgs>
  | GraphQLOperationConfig;

/**
 * Async operation state
 */
export interface AsyncOperationState {
  isLoading: boolean;
  isMutating: boolean;
  error: Error | null;
  isSuccess: boolean;
}

/**
 * Unified operation return type
 */
export interface UnifiedOperationReturn<TEntity = any, TCreateArgs extends unknown[] = unknown[]> {
  // Data state
  data: TEntity[] | null;
  dataMap: Map<string, TEntity> | null;
  count: number;

  // Async state
  state: AsyncOperationState;

  // CRUD operations
  create: (...args: TCreateArgs) => Promise<string | null>;
  update: (id: string, updates: Partial<TEntity>) => Promise<boolean>;
  remove: (id: string) => Promise<boolean>;
  refresh?: () => Promise<void>;

  // Utilities
  getById: (id: string) => TEntity | undefined;
  exists: (id: string) => boolean;
  clearError: () => void;
  reset: () => void;
}

/**
 * Hook for managing async operation state
 */
export function useAsyncState(): [AsyncOperationState, {
  setLoading: (loading: boolean) => void;
  setMutating: (mutating: boolean) => void;
  setError: (error: Error | null) => void;
  setSuccess: (success: boolean) => void;
  reset: () => void;
}] {
  const [state, setState] = useState<AsyncOperationState>({
    isLoading: false,
    isMutating: false,
    error: null,
    isSuccess: false,
  });

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, isLoading: loading }));
  }, []);

  const setMutating = useCallback((mutating: boolean) => {
    setState(prev => ({ ...prev, isMutating: mutating }));
  }, []);

  const setError = useCallback((error: Error | null) => {
    setState(prev => ({ ...prev, error, isSuccess: false }));
  }, []);

  const setSuccess = useCallback((success: boolean) => {
    setState(prev => ({ ...prev, isSuccess: success, error: null }));
  }, []);

  const reset = useCallback(() => {
    setState({
      isLoading: false,
      isMutating: false,
      error: null,
      isSuccess: false,
    });
  }, []);

  return [state, { setLoading, setMutating, setError, setSuccess, reset }];
}

/**
 * Creates a unified operation hook that works with both store and GraphQL
 */
export function useOperationFactory<TEntity = any, TCreateArgs extends unknown[] = unknown[]>(
  config: UnifiedOperationConfig<TEntity, TCreateArgs>
): UnifiedOperationReturn<TEntity, TCreateArgs> {
  const [asyncState, asyncActions] = useAsyncState();

  // Handle store operations
  if (config.type === 'store') {
    // Use the existing store operation factory
    const useStoreHook = createStoreOperationHook(config);
    const storeOperations = useStoreHook();

    // Adapt store operations to unified interface
    return useMemo(() => ({
      // Data state
      data: storeOperations.items,
      dataMap: storeOperations.itemsMap,
      count: storeOperations.count,

      // Async state
      state: {
        isLoading: false, // Store operations are synchronous
        isMutating: storeOperations.isProcessing,
        error: Object.keys(storeOperations.errors).length > 0
          ? new Error(Object.values(storeOperations.errors)[0])
          : null,
        isSuccess: !storeOperations.isProcessing && Object.keys(storeOperations.errors).length === 0,
      },

      // CRUD operations
      create: storeOperations.add,
      update: storeOperations.update,
      remove: storeOperations.delete,
      refresh: undefined, // Store doesn't need refresh

      // Utilities
      getById: storeOperations.getById,
      exists: storeOperations.exists,
      clearError: storeOperations.clearErrors,
      reset: () => {
        storeOperations.clearErrors();
        storeOperations.setDirty(false);
      },
    }), [storeOperations]);
  }

  // Handle GraphQL operations
  const { entityName, documents, messages, options = { showToasts: true } } = config as GraphQLOperationConfig;

  // Create GraphQL hooks
  const queryHook = documents.list ? createEntityQuery({
    entityName,
    document: documents.list,
    cacheStrategy: config.cacheStrategy,
    silent: !options.showToasts,
  }) : null;

  const createMutationHook = documents.create ? createEntityMutation({
    entityName,
    document: documents.create,
    successMessage: messages?.addSuccess,
    errorMessage: messages?.addError,
    silent: !options.showToasts,
  }) : null;

  const updateMutationHook = documents.update ? createEntityMutation({
    entityName,
    document: documents.update,
    successMessage: messages?.updateSuccess,
    errorMessage: messages?.updateError,
    silent: !options.showToasts,
  }) : null;

  const deleteMutationHook = documents.delete ? createEntityMutation({
    entityName,
    document: documents.delete,
    successMessage: messages?.deleteSuccess,
    errorMessage: messages?.deleteError,
    silent: !options.showToasts,
  }) : null;

  // Use hooks
  const queryResult = queryHook ? queryHook() : null;
  const [createMutation, createResult] = createMutationHook ? createMutationHook() : [null, null];
  const [updateMutation, updateResult] = updateMutationHook ? updateMutationHook() : [null, null];
  const [deleteMutation, deleteResult] = deleteMutationHook ? deleteMutationHook() : [null, null];

  // Convert data to map for consistency
  const dataMap = useMemo(() => {
    if (!queryResult?.data) return new Map();
    const data = Array.isArray(queryResult.data) ? queryResult.data : [queryResult.data];
    return new Map(data.map((item: any) => [item.id || item._id, item]));
  }, [queryResult?.data]);

  const dataArray = useMemo(() => Array.from(dataMap.values()), [dataMap]);

  // CRUD operations
  const create = useCallback(async (...args: TCreateArgs): Promise<string | null> => {
    if (!createMutation) {
      console.error(`Create mutation not configured for ${entityName}`);
      return null;
    }

    try {
      asyncActions.setMutating(true);
      const result = await createMutation({ variables: args[0] as any });
      const id = result.data?.id || result.data?._id || null;
      asyncActions.setSuccess(true);
      return id;
    } catch (error) {
      asyncActions.setError(error as Error);
      return null;
    } finally {
      asyncActions.setMutating(false);
    }
  }, [createMutation, entityName, asyncActions]);

  const update = useCallback(async (id: string, updates: Partial<TEntity>): Promise<boolean> => {
    if (!updateMutation) {
      console.error(`Update mutation not configured for ${entityName}`);
      return false;
    }

    try {
      asyncActions.setMutating(true);
      await updateMutation({ variables: { id, ...updates } });
      asyncActions.setSuccess(true);
      return true;
    } catch (error) {
      asyncActions.setError(error as Error);
      return false;
    } finally {
      asyncActions.setMutating(false);
    }
  }, [updateMutation, entityName, asyncActions]);

  const remove = useCallback(async (id: string): Promise<boolean> => {
    if (!deleteMutation) {
      console.error(`Delete mutation not configured for ${entityName}`);
      return false;
    }

    try {
      asyncActions.setMutating(true);
      await deleteMutation({ variables: { id } });
      asyncActions.setSuccess(true);
      return true;
    } catch (error) {
      asyncActions.setError(error as Error);
      return false;
    } finally {
      asyncActions.setMutating(false);
    }
  }, [deleteMutation, entityName, asyncActions]);

  const refresh = useCallback(async () => {
    if (!queryResult?.refetch) return;

    try {
      asyncActions.setLoading(true);
      await queryResult.refetch();
      asyncActions.setSuccess(true);
    } catch (error) {
      asyncActions.setError(error as Error);
    } finally {
      asyncActions.setLoading(false);
    }
  }, [queryResult, asyncActions]);

  // Utilities
  const getById = useCallback((id: string): TEntity | undefined => {
    return dataMap.get(id);
  }, [dataMap]);

  const exists = useCallback((id: string): boolean => {
    return dataMap.has(id);
  }, [dataMap]);

  const clearError = useCallback(() => {
    asyncActions.setError(null);
  }, [asyncActions]);

  const reset = useCallback(() => {
    asyncActions.reset();
  }, [asyncActions]);

  // Combine async states
  const combinedAsyncState: AsyncOperationState = {
    isLoading: queryResult?.loading || asyncState.isLoading,
    isMutating: createResult?.loading || updateResult?.loading || deleteResult?.loading || asyncState.isMutating,
    error: queryResult?.error || createResult?.error || updateResult?.error || deleteResult?.error || asyncState.error,
    isSuccess: asyncState.isSuccess,
  };

  return {
    // Data state
    data: dataArray,
    dataMap,
    count: dataMap.size,

    // Async state
    state: combinedAsyncState,

    // CRUD operations
    create,
    update,
    remove,
    refresh: queryResult ? refresh : undefined,

    // Utilities
    getById,
    exists,
    clearError,
    reset,
  };
}

/**
 * Create a simple store operation hook for entities that only need basic CRUD
 */
export function createSimpleStoreOperations<TEntity>(
  entityName: string,
  selectors: {
    collection: (state: any) => Map<string, TEntity>;
    add: (state: any) => (...args: any[]) => string;
    update: (state: any) => (...args: any[]) => void;
    remove: (state: any) => (...args: any[]) => void;
  }
) {
  return useOperationFactory<TEntity>({
    type: 'store',
    entityName,
    selectCollection: selectors.collection,
    selectAddAction: selectors.add,
    selectUpdateAction: selectors.update as any,
    selectDeleteAction: selectors.remove as any,
  });
}
