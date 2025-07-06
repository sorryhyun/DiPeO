import { ApolloCache, DocumentNode, OperationVariables } from '@apollo/client';

/**
 * Common cache update strategies for GraphQL operations
 */

/**
 * Strategy for adding an item to a list in the cache
 */
export function addToListStrategy<T, TData = Record<string, unknown>, TVariables = OperationVariables>(
  cache: ApolloCache<TData>,
  query: DocumentNode,
  variables: TVariables,
  newItem: T,
  listField: string,
  keyField: string = 'id'
) {
  const data = cache.readQuery<TData>({ query, variables });
  if (data && (data as Record<string, unknown>)[listField]) {
    cache.writeQuery({
      query,
      variables,
      data: {
        ...data,
        [listField]: [...((data as Record<string, unknown>)[listField] as T[]), newItem]
      }
    });
  }
}

/**
 * Strategy for removing an item from a list in the cache
 */
export function removeFromListStrategy<T extends Record<string, unknown>, TData = Record<string, unknown>, TVariables = OperationVariables>(
  cache: ApolloCache<TData>,
  query: DocumentNode,
  variables: TVariables,
  itemId: string,
  listField: string,
  keyField: string = 'id'
) {
  const data = cache.readQuery<TData>({ query, variables });
  if (data && (data as Record<string, unknown>)[listField]) {
    cache.writeQuery({
      query,
      variables,
      data: {
        ...data,
        [listField]: ((data as Record<string, unknown>)[listField] as T[]).filter((item: T) => item[keyField] !== itemId)
      }
    });
  }
}

/**
 * Strategy for updating an item in a list in the cache
 */
export function updateInListStrategy<T extends Record<string, unknown>, TData = Record<string, unknown>, TVariables = OperationVariables>(
  cache: ApolloCache<TData>,
  query: DocumentNode,
  variables: TVariables,
  updatedItem: T,
  listField: string,
  keyField: string = 'id'
) {
  const data = cache.readQuery<TData>({ query, variables });
  if (data && (data as Record<string, unknown>)[listField]) {
    cache.writeQuery({
      query,
      variables,
      data: {
        ...data,
        [listField]: ((data as Record<string, unknown>)[listField] as T[]).map((item: T) => 
          item[keyField] === updatedItem[keyField] ? updatedItem : item
        )
      }
    });
  }
}

/**
 * Strategy for optimistic response generation
 */
export function createOptimisticResponse<T>(
  typename: string,
  tempId: string,
  data: Partial<T>
): T {
  return {
    __typename: typename,
    id: tempId,
    ...data
  } as T;
}

/**
 * Strategy for cache eviction after mutations
 */
export function evictFromCache<T = unknown>(
  cache: ApolloCache<T>,
  typename: string,
  id: string
) {
  cache.evict({
    id: cache.identify({ __typename: typename, id })
  });
  cache.gc();
}

/**
 * Common refetch queries configuration
 */
export interface RefetchConfig<TVariables = OperationVariables> {
  queries: Array<{
    query: DocumentNode;
    variables?: TVariables;
  }>;
}

export function createRefetchQueries<TVariables = OperationVariables>(config: RefetchConfig<TVariables>) {
  return config.queries.map(({ query, variables }) => ({
    query,
    variables: variables || {}
  }));
}