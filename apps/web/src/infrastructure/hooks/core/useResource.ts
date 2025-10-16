import { useState, useCallback, useRef, useEffect } from 'react';
import { ApolloError } from '@apollo/client';
import { toast } from 'sonner';

export type ResourceState<T> = {
  data: T | null;
  loading: boolean;
  error: Error | null;
  updating: boolean;
  deleting: boolean;
  lastFetch: Date | null;
};

export type ResourceOperations<T> = {
  fetch?: (id?: string) => Promise<T>;
  list?: (params?: Record<string, any>) => Promise<T[]>;
  create?: (data: Partial<T>) => Promise<T>;
  update?: (id: string, data: Partial<T>) => Promise<T>;
  delete?: (id: string) => Promise<boolean>;
  validate?: (data: Partial<T>) => Promise<ValidationResult>;
};

export type ValidationResult = {
  isValid: boolean;
  errors: Record<string, string[]>;
};

export type UseResourceOptions = {
  showToasts?: boolean;
  optimisticUpdates?: boolean;
  autoRefetch?: boolean;
  refetchInterval?: number;
  onSuccess?: (operation: string, data?: any) => void;
  onError?: (operation: string, error: Error) => void;
};

export type UseResourceReturn<T> = {
  data: T | null;
  loading: boolean;
  error: Error | null;
  updating: boolean;
  deleting: boolean;

  fetch: (id?: string) => Promise<void>;
  list: (params?: Record<string, any>) => Promise<T[]>;
  create: (data: Partial<T>) => Promise<T | null>;
  update: (id: string, data: Partial<T>) => Promise<T | null>;
  delete: (id: string) => Promise<boolean>;

  refetch: () => Promise<void>;
  clearError: () => void;
  reset: () => void;

  isStale: boolean;
  lastFetch: Date | null;
};

const DEFAULT_OPTIONS: UseResourceOptions = {
  showToasts: true,
  optimisticUpdates: false,
  autoRefetch: false,
  refetchInterval: 60000,
};

export function useResource<T extends { id?: string } = any>(
  resource: string,
  operations: ResourceOperations<T>,
  options: UseResourceOptions = {}
): UseResourceReturn<T> {
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options };
  const { showToasts, optimisticUpdates, autoRefetch, refetchInterval, onSuccess, onError } = mergedOptions;

  const [state, setState] = useState<ResourceState<T>>({
    data: null,
    loading: false,
    error: null,
    updating: false,
    deleting: false,
    lastFetch: null,
  });

  const currentIdRef = useRef<string | undefined>(undefined);
  const refetchTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const previousDataRef = useRef<T | null>(null);

  const isStale = state.lastFetch
    ? new Date().getTime() - state.lastFetch.getTime() > refetchInterval!
    : true;

  const handleError = useCallback((operation: string, error: unknown) => {
    const errorObj = error instanceof Error ? error : new Error(String(error));

    setState(prev => ({
      ...prev,
      loading: false,
      updating: false,
      deleting: false,
      error: errorObj,
    }));

    if (showToasts) {
      const message = error instanceof ApolloError
        ? error.message
        : `Failed to ${operation} ${resource}`;
      toast.error(message);
    }

    onError?.(operation, errorObj);
  }, [resource, showToasts, onError]);

  const handleSuccess = useCallback((operation: string, data?: T) => {
    if (showToasts && operation !== 'fetch') {
      const message = operation === 'delete'
        ? `${resource} deleted successfully`
        : `${resource} ${operation}d successfully`;
      toast.success(message);
    }

    onSuccess?.(operation, data);
  }, [resource, showToasts, onSuccess]);

  const fetch = useCallback(async (id?: string) => {
    if (!operations.fetch) {
      console.warn(`No fetch operation defined for ${resource}`);
      return;
    }

    currentIdRef.current = id;
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const data = await operations.fetch(id);
      setState(prev => ({
        ...prev,
        data,
        loading: false,
        lastFetch: new Date(),
      }));
      handleSuccess('fetch', data);
    } catch (error) {
      handleError('fetch', error);
    }
  }, [operations, handleSuccess, handleError]);

  const list = useCallback(async (params?: Record<string, any>): Promise<T[]> => {
    if (!operations.list) {
      console.warn(`No list operation defined for ${resource}`);
      return [];
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const data = await operations.list(params);
      setState(prev => ({
        ...prev,
        loading: false,
        lastFetch: new Date(),
      }));
      handleSuccess('list', data as TData);
      return data;
    } catch (error) {
      handleError('list', error);
      return [];
    }
  }, [operations, handleSuccess, handleError]);

  const create = useCallback(async (data: Partial<T>): Promise<T | null> => {
    if (!operations.create) {
      console.warn(`No create operation defined for ${resource}`);
      return null;
    }

    if (operations.validate) {
      const validation = await operations.validate(data);
      if (!validation.isValid) {
        const firstError = Object.values(validation.errors)[0]?.[0];
        handleError('validate', new Error(firstError || 'Validation failed'));
        return null;
      }
    }

    setState(prev => ({ ...prev, updating: true, error: null }));

    try {
      const result = await operations.create(data);
      setState(prev => ({
        ...prev,
        data: result,
        updating: false,
        lastFetch: new Date(),
      }));
      handleSuccess('create', result);
      return result;
    } catch (error) {
      handleError('create', error);
      return null;
    }
  }, [operations, resource, handleSuccess, handleError]);

  const update = useCallback(async (id: string, data: Partial<T>): Promise<T | null> => {
    if (!operations.update) {
      console.warn(`No update operation defined for ${resource}`);
      return null;
    }

    if (operations.validate) {
      const validation = await operations.validate(data);
      if (!validation.isValid) {
        const firstError = Object.values(validation.errors)[0]?.[0];
        handleError('validate', new Error(firstError || 'Validation failed'));
        return null;
      }
    }

    setState(prev => ({ ...prev, updating: true, error: null }));

    if (optimisticUpdates && state.data) {
      previousDataRef.current = state.data;
      setState(prev => ({
        ...prev,
        data: { ...prev.data!, ...data },
      }));
    }

    try {
      const result = await operations.update(id, data);
      setState(prev => ({
        ...prev,
        data: result,
        updating: false,
        lastFetch: new Date(),
      }));
      handleSuccess('update', result);
      return result;
    } catch (error) {
      if (optimisticUpdates && previousDataRef.current) {
        setState(prev => ({
          ...prev,
          data: previousDataRef.current,
        }));
      }
      handleError('update', error);
      return null;
    }
  }, [operations, resource, optimisticUpdates, state.data, handleSuccess, handleError]);

  const deleteResource = useCallback(async (id: string): Promise<boolean> => {
    if (!operations.delete) {
      console.warn(`No delete operation defined for ${resource}`);
      return false;
    }

    setState(prev => ({ ...prev, deleting: true, error: null }));

    try {
      const success = await operations.delete(id);
      if (success) {
        setState(prev => ({
          ...prev,
          data: null,
          deleting: false,
        }));
        handleSuccess('delete');
      }
      return success;
    } catch (error) {
      handleError('delete', error);
      return false;
    }
  }, [operations, resource, handleSuccess, handleError]);

  const refetch = useCallback(async () => {
    if (currentIdRef.current !== undefined && operations.fetch) {
      await fetch(currentIdRef.current);
    }
  }, [fetch, operations.fetch]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
      updating: false,
      deleting: false,
      lastFetch: null,
    });
    currentIdRef.current = undefined;
    if (refetchTimerRef.current) {
      clearInterval(refetchTimerRef.current);
    }
  }, []);

  useEffect(() => {
    if (autoRefetch && !state.loading && !state.updating && !state.deleting) {
      refetchTimerRef.current = setInterval(() => {
        if (isStale) {
          void refetch();
        }
      }, refetchInterval);
    }

    return () => {
      if (refetchTimerRef.current) {
        clearInterval(refetchTimerRef.current);
      }
    };
  }, [autoRefetch, refetchInterval, isStale, refetch, state.loading, state.updating, state.deleting]);

  useEffect(() => {
    return () => {
      if (refetchTimerRef.current) {
        clearInterval(refetchTimerRef.current);
      }
    };
  }, []);

  return {
    data: state.data,
    loading: state.loading,
    error: state.error,
    updating: state.updating,
    deleting: state.deleting,

    fetch,
    list,
    create,
    update,
    delete: deleteResource,

    refetch,
    clearError,
    reset,

    isStale,
    lastFetch: state.lastFetch,
  };
}
