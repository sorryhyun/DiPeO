import {
  DocumentNode,
  useQuery,
  useMutation,
  useSubscription,
  QueryHookOptions,
  MutationHookOptions,
  SubscriptionHookOptions,
  ApolloError,
  OperationVariables
} from '@apollo/client';
import { toast } from 'sonner';
import { useCallback } from 'react';

/**
 * Factory configuration for creating standardized GraphQL operations
 */

export interface EntityQueryConfig<TData = any, TVariables extends OperationVariables = OperationVariables> {
  // Entity name for error messages and logging
  entityName: string;

  // GraphQL document
  document: DocumentNode;

  // Options for the specific operation type
  options?: QueryHookOptions<TData, TVariables> |
           MutationHookOptions<TData, TVariables> |
           SubscriptionHookOptions<TData, TVariables>;

  // Success handling
  onSuccess?: (data: TData) => void;

  // Error handling override (if not provided, uses default toast)
  onError?: (error: ApolloError) => void;

  // Custom success message (for mutations)
  successMessage?: string | ((data: TData) => string);

  // Custom error message
  errorMessage?: string | ((error: ApolloError) => string);

  // Disable automatic error toasts
  silent?: boolean;

  // Cache configuration
  cacheStrategy?: 'cache-first' | 'cache-and-network' | 'network-only' | 'no-cache' | 'cache-only';
}

/**
 * Standard error handler with toast notifications
 */
const handleError = (
  error: ApolloError,
  entityName: string,
  operation: string,
  customMessage?: string | ((error: ApolloError) => string),
  silent?: boolean
) => {
  // Check if this is likely a server shutdown error
  const isServerShutdown = error.networkError && (
    error.message.includes('Failed to fetch') ||
    error.message.includes('NetworkError') ||
    error.message.includes('fetch failed')
  );

  // Check if we're in CLI monitor mode
  const params = new URLSearchParams(window.location.search);
  const isCliMonitorMode = params.get('monitor') === 'true' && params.get('no-auto-exit') === 'true';

  // Suppress errors if server is shutting down in CLI mode
  if (isServerShutdown && isCliMonitorMode) {
    console.log(`[${entityName}] Server appears to be shutting down, suppressing error`);
    return;
  }

  const message = typeof customMessage === 'function'
    ? customMessage(error)
    : customMessage || `Failed to ${operation} ${entityName}: ${error.message}`;

  if (!silent) {
    toast.error(message);
  }

  console.error(`[${entityName}] ${operation} error:`, error);
};

/**
 * Standard success handler with optional toast notifications
 */
const handleSuccess = <TData>(
  data: TData,
  entityName: string,
  operation: string,
  customMessage?: string | ((data: TData) => string),
  silent?: boolean
) => {
  if (!silent && customMessage) {
    const message = typeof customMessage === 'function'
      ? customMessage(data)
      : customMessage;
    toast.success(message);
  }
};

/**
 * Create a standardized query hook
 */
export function createEntityQuery<TData = any, TVariables extends OperationVariables = OperationVariables>(
  config: EntityQueryConfig<TData, TVariables>
) {
  return (variables?: TVariables, overrideOptions?: QueryHookOptions<TData, TVariables>) => {
    const mergedOptions: QueryHookOptions<TData, TVariables> = {
      fetchPolicy: config.cacheStrategy || 'cache-first',
      errorPolicy: 'all',
      ...config.options,
      ...overrideOptions,
      variables: variables || config.options?.variables,
      onError: (error) => {
        if (config.onError) {
          config.onError(error);
        } else {
          handleError(error, config.entityName, 'fetch', config.errorMessage, config.silent);
        }
        overrideOptions?.onError?.(error);
      },
      onCompleted: (data) => {
        if (config.onSuccess) {
          config.onSuccess(data);
        }
        handleSuccess(data, config.entityName, 'fetch', config.successMessage, config.silent);
        overrideOptions?.onCompleted?.(data);
      }
    };

    return useQuery<TData, TVariables>(config.document, mergedOptions);
  };
}

/**
 * Create a standardized mutation hook
 */
export function createEntityMutation<TData = any, TVariables extends OperationVariables = OperationVariables>(
  config: EntityQueryConfig<TData, TVariables>
) {
  return (overrideOptions?: MutationHookOptions<TData, TVariables>) => {
    const mergedOptions: MutationHookOptions<TData, TVariables> = {
      errorPolicy: 'all',
      ...config.options,
      ...overrideOptions,
      // Remove fetchPolicy if it was set in config.options since it's not valid for mutations
      fetchPolicy: undefined,
      onError: (error) => {
        if (config.onError) {
          config.onError(error);
        } else {
          handleError(error, config.entityName, 'mutate', config.errorMessage, config.silent);
        }
        overrideOptions?.onError?.(error);
      },
      onCompleted: (data) => {
        if (config.onSuccess) {
          config.onSuccess(data);
        }
        handleSuccess(data, config.entityName, 'mutate', config.successMessage, config.silent);
        overrideOptions?.onCompleted?.(data);
      }
    };

    const [mutationFn, result] = useMutation<TData, TVariables>(config.document, mergedOptions);

    // Wrap mutation function to handle errors consistently
    const wrappedMutation = useCallback(async (options?: Parameters<typeof mutationFn>[0]) => {
      return await mutationFn(options);
    }, [mutationFn]);

    return [wrappedMutation, result] as const;
  };
}

/**
 * Create a standardized subscription hook
 */
export function createEntitySubscription<TData = any, TVariables extends OperationVariables = OperationVariables>(
  config: EntityQueryConfig<TData, TVariables>
) {
  return (variables?: TVariables, overrideOptions?: SubscriptionHookOptions<TData, TVariables>) => {
    const mergedOptions: SubscriptionHookOptions<TData, TVariables> = {
      ...config.options,
      ...overrideOptions,
      variables: variables || config.options?.variables,
      // Remove cache-and-network if it was set, as it's not valid for subscriptions
      fetchPolicy: config.cacheStrategy === 'cache-and-network' ? 'network-only' :
                   (config.cacheStrategy as any) || config.options?.fetchPolicy || overrideOptions?.fetchPolicy,
      onError: (error) => {
        if (config.onError) {
          config.onError(error);
        } else {
          handleError(error, config.entityName, 'subscribe', config.errorMessage, config.silent);
        }
        overrideOptions?.onError?.(error);
      },
      onData: (data) => {
        if (data.data.data && config.onSuccess) {
          config.onSuccess(data.data.data);
        }
        overrideOptions?.onData?.(data);
      }
    };

    return useSubscription<TData, TVariables>(config.document, mergedOptions);
  };
}

/**
 * Create a complete entity operations hook with queries, mutations, and subscriptions
 */
export interface EntityOperationsConfig {
  entityName: string;
  queries?: Record<string, EntityQueryConfig>;
  mutations?: Record<string, EntityQueryConfig>;
  subscriptions?: Record<string, EntityQueryConfig>;
}

export function createEntityOperations(config: EntityOperationsConfig) {
  const queries: Record<string, ReturnType<typeof createEntityQuery>> = {};
  const mutations: Record<string, ReturnType<typeof createEntityMutation>> = {};
  const subscriptions: Record<string, ReturnType<typeof createEntitySubscription>> = {};

  // Create query hooks
  if (config.queries) {
    Object.entries(config.queries).forEach(([key, queryConfig]) => {
      queries[key] = createEntityQuery({
        ...queryConfig,
        entityName: config.entityName
      });
    });
  }

  // Create mutation hooks
  if (config.mutations) {
    Object.entries(config.mutations).forEach(([key, mutationConfig]) => {
      mutations[key] = createEntityMutation({
        ...mutationConfig,
        entityName: config.entityName
      });
    });
  }

  // Create subscription hooks
  if (config.subscriptions) {
    Object.entries(config.subscriptions).forEach(([key, subscriptionConfig]) => {
      subscriptions[key] = createEntitySubscription({
        ...subscriptionConfig,
        entityName: config.entityName
      });
    });
  }

  return {
    queries,
    mutations,
    subscriptions
  };
}
