/**
 * useExecutionProvider - Provides GraphQL execution implementation
 * 
 * This hook now always returns the GraphQL implementation as part of the migration
 * from REST/WebSocket to GraphQL.
 */

import { useExecutionGraphQL } from './useExecutionGraphQL';
import type { UseExecutionOptions, UseExecutionReturn } from './useExecution';

/**
 * Returns the GraphQL execution hook implementation.
 * 
 * @param options - Execution hook options
 * @returns GraphQL execution hook implementation
 */
export function useExecutionProvider(options: UseExecutionOptions = {}): UseExecutionReturn {
  console.log('[ExecutionProvider] Using GraphQL execution');
  return useExecutionGraphQL(options);
}