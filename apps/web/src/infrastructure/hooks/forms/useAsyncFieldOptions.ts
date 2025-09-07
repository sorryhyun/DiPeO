import { useQuery, UseQueryResult, useQueries } from '@tanstack/react-query';
import { useMemo } from 'react';
import type { AsyncFieldOptions, FormState } from '@/domain/diagram/forms/types';

interface UseAsyncFieldOptionsParams<T extends Record<string, any>> {
  field: string;
  options: AsyncFieldOptions;
  formState: FormState<T>;
}

export function useAsyncFieldOptions<T extends Record<string, any>, Option = any>({
  field,
  options,
  formState,
}: UseAsyncFieldOptionsParams<T>): UseQueryResult<Option[], Error> & {
  isEnabled: boolean;
} {
  const { queryKey, queryFn, dependencies = [], enabled = true } = options;

  const dependencyValues = useMemo(
    () => dependencies.map(dep => formState.data[dep]),
    [dependencies, formState.data]
  );

  const isEnabled = useMemo(() => {
    if (!enabled) return false;

    return dependencies.every(dep => {
      const value = formState.data[dep];
      return value !== undefined && value !== null && value !== '';
    });
  }, [enabled, dependencies, formState.data]);

  const fullQueryKey = useMemo(
    () => [...queryKey, field, ...dependencyValues],
    [queryKey, field, dependencyValues]
  );

  const query = useQuery<Option[], Error>({
    queryKey: fullQueryKey,
    queryFn,
    enabled: isEnabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  return {
    ...query,
    isEnabled,
  };
}

export function useMultipleAsyncFieldOptions<T extends Record<string, any>>(
  fields: Record<string, AsyncFieldOptions>,
  formState: FormState<T>
) {
  // Convert fields object to a stable array
  const fieldEntries = useMemo(
    () => Object.entries(fields),
    [fields]
  );

  // Extract all unique dependencies from all fields
  const allDependencies = useMemo(() => {
    const deps = new Set<string>();
    fieldEntries.forEach(([, options]) => {
      (options.dependencies || []).forEach(dep => deps.add(dep));
    });
    return Array.from(deps);
  }, [fieldEntries]);

  // Track only the dependency values we care about
  const trackedDependencyValues = useMemo(() => {
    const values: Record<string, unknown> = {};
    allDependencies.forEach(dep => {
      values[dep] = formState.data[dep];
    });
    return values;
  }, [allDependencies, formState.data]);

  // Create stable query configurations
  const queryConfigs = useMemo(() => {
    return fieldEntries.map(([field, options]) => {
      const { queryKey, queryFn, dependencies = [], enabled = true } = options;

      // Calculate if query should be enabled based on dependencies
      const hasAllDependencies = dependencies.length === 0 || dependencies.every(dep => {
        const value = trackedDependencyValues[dep];
        return value !== undefined && value !== null && value !== '';
      });

      const isEnabled = enabled && hasAllDependencies;

      // Create dependency values for query key
      const dependencyValues = dependencies.map(dep => trackedDependencyValues[dep]);

      return {
        queryKey: [...queryKey, field, ...dependencyValues].filter(v => v !== undefined),
        queryFn,
        enabled: isEnabled,
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes
      };
    });
  }, [fieldEntries, trackedDependencyValues]);

  // Use useQueries to handle multiple queries properly
  const queryResults = useQueries({
    queries: queryConfigs,
  });

  // Map results back to field names
  const queries = useMemo(() => {
    return fieldEntries.reduce((acc, [field], index) => {
      const queryResult = queryResults[index];
      const options = fields[field];

      if (!options || !queryResult) {
        return acc;
      }

      const { dependencies = [], enabled = true } = options;

      const isEnabled = enabled && dependencies.every((dep: string) => {
        const value = trackedDependencyValues[dep];
        return value !== undefined && value !== null && value !== '';
      });

      acc[field] = {
        ...queryResult,
        isEnabled,
      } as UseQueryResult<any, Error> & { isEnabled: boolean };
      return acc;
    }, {} as Record<string, UseQueryResult<any, Error> & { isEnabled: boolean }>);
  }, [fieldEntries, queryResults, fields, trackedDependencyValues]);

  const isLoading = queryResults.some(query => query.isLoading);
  const hasError = queryResults.some(query => query.isError);

  return {
    queries,
    isLoading,
    hasError,
  };
}
