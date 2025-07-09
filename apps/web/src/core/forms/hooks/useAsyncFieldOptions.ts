import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { useMemo } from 'react';
import type { AsyncFieldOptions, FormState } from '../types';

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
  const queries = useMemo(() => {
    return Object.entries(fields).reduce((acc, [field, options]) => {
      acc[field] = useAsyncFieldOptions({
        field,
        options,
        formState,
      });
      return acc;
    }, {} as Record<string, ReturnType<typeof useAsyncFieldOptions>>);
  }, [fields, formState]);

  const isLoading = Object.values(queries).some(query => query.isLoading);
  const hasError = Object.values(queries).some(query => query.isError);

  return {
    queries,
    isLoading,
    hasError,
  };
}