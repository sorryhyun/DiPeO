import { ApolloCache } from '@apollo/client';

/**
 * Common cache update strategies for GraphQL operations
 */

/**
 * Strategy for adding an item to a list in the cache
 */
export function addToListStrategy<T>(
  cache: ApolloCache<any>,
  query: any,
  variables: any,
  newItem: T,
  listField: string,
  keyField: string = 'id'
) {
  const data = cache.readQuery<Record<string, any>>({ query, variables });
  if (data && data[listField]) {
    cache.writeQuery({
      query,
      variables,
      data: {
        ...data,
        [listField]: [...data[listField], newItem]
      }
    });
  }
}

/**
 * Strategy for removing an item from a list in the cache
 */
export function removeFromListStrategy<T extends { [key: string]: any }>(
  cache: ApolloCache<any>,
  query: any,
  variables: any,
  itemId: string,
  listField: string,
  keyField: string = 'id'
) {
  const data = cache.readQuery<Record<string, any>>({ query, variables });
  if (data && data[listField]) {
    cache.writeQuery({
      query,
      variables,
      data: {
        ...data,
        [listField]: data[listField].filter((item: T) => item[keyField] !== itemId)
      }
    });
  }
}

/**
 * Strategy for updating an item in a list in the cache
 */
export function updateInListStrategy<T extends { [key: string]: any }>(
  cache: ApolloCache<any>,
  query: any,
  variables: any,
  updatedItem: T,
  listField: string,
  keyField: string = 'id'
) {
  const data = cache.readQuery<Record<string, any>>({ query, variables });
  if (data && data[listField]) {
    cache.writeQuery({
      query,
      variables,
      data: {
        ...data,
        [listField]: data[listField].map((item: T) => 
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
export function evictFromCache(
  cache: ApolloCache<any>,
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
export interface RefetchConfig {
  queries: Array<{
    query: any;
    variables?: any;
  }>;
}

export function createRefetchQueries(config: RefetchConfig) {
  return config.queries.map(({ query, variables }) => ({
    query,
    variables: variables || {}
  }));
}