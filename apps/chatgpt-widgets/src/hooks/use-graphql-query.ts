/**
 * Hook for executing GraphQL queries with loading and error states
 */

import { useEffect, useState } from 'react';
import { queryGraphQL, GraphQLResponse } from '../lib/graphql-client';

interface QueryState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Execute a GraphQL query and manage loading/error states
 */
export function useGraphQLQuery<T = any>(
  query: string,
  variables?: Record<string, any>,
  options: { skip?: boolean; refetchInterval?: number } = {}
): QueryState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<QueryState<T>>({
    data: null,
    loading: !options.skip,
    error: null,
  });

  const executeQuery = async () => {
    if (options.skip) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response: GraphQLResponse<T> = await queryGraphQL(query, variables);

      if (response.errors) {
        throw new Error(response.errors[0]?.message || 'GraphQL query failed');
      }

      setState({
        data: response.data || null,
        loading: false,
        error: null,
      });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error instanceof Error ? error : new Error('Unknown error'),
      });
    }
  };

  useEffect(() => {
    executeQuery();

    // Set up refetch interval if specified
    if (options.refetchInterval) {
      const interval = setInterval(executeQuery, options.refetchInterval);
      return () => clearInterval(interval);
    }
  }, [query, JSON.stringify(variables), options.skip, options.refetchInterval]);

  return {
    ...state,
    refetch: executeQuery,
  };
}
