/**
 * Hook for executing GraphQL queries with loading and error states
 */

import { useEffect, useState, useMemo, useRef } from 'react';
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

  // Stabilize variables to prevent infinite re-renders
  const stableVariables = useMemo(() => variables, [JSON.stringify(variables)]);

  // Track if component is mounted to prevent state updates after unmount
  const isMountedRef = useRef(true);

  const executeQuery = async () => {
    if (options.skip || !isMountedRef.current) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response: GraphQLResponse<T> = await queryGraphQL(query, stableVariables);

      if (!isMountedRef.current) return; // Abort if unmounted

      if (response.errors) {
        throw new Error(response.errors[0]?.message || 'GraphQL query failed');
      }

      setState({
        data: response.data || null,
        loading: false,
        error: null,
      });
    } catch (error) {
      if (!isMountedRef.current) return; // Abort if unmounted

      setState({
        data: null,
        loading: false,
        error: error instanceof Error ? error : new Error('Unknown error'),
      });
    }
  };

  useEffect(() => {
    isMountedRef.current = true;
    executeQuery();

    // Set up refetch interval if specified
    let interval: NodeJS.Timeout | undefined;
    if (options.refetchInterval) {
      interval = setInterval(executeQuery, options.refetchInterval);
    }

    return () => {
      isMountedRef.current = false;
      if (interval) clearInterval(interval);
    };
  }, [query, stableVariables, options.skip, options.refetchInterval]);

  return {
    ...state,
    refetch: executeQuery,
  };
}
