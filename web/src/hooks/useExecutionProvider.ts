/**
 * useExecutionProvider - Provides either WebSocket or GraphQL execution based on feature flag
 * 
 * This hook checks for a feature flag and returns the appropriate execution implementation.
 */

import { useExecution } from './useExecution';
import { useExecutionGraphQL } from './useExecutionGraphQL';
import type { UseExecutionOptions, UseExecutionReturn } from './useExecution';

/**
 * Returns the appropriate execution hook based on feature flag.
 * 
 * Feature flag can be set via:
 * - URL parameter: ?useGraphQL=true
 * - Environment variable: VITE_USE_GRAPHQL=true
 * 
 * @param options - Execution hook options
 * @returns Execution hook implementation
 */
export function useExecutionProvider(options: UseExecutionOptions = {}): UseExecutionReturn {
  // Check URL parameter
  const params = new URLSearchParams(window.location.search);
  const urlFlag = params.get('useGraphQL') === 'true' || params.get('graphql') === 'true';
  
  // Check environment variable
  const envFlag = import.meta.env.VITE_USE_GRAPHQL === 'true';
  
  // Use GraphQL if either flag is set
  const useGraphQL = urlFlag || envFlag;
  
  if (useGraphQL) {
    console.log('[ExecutionProvider] Using GraphQL execution');
    return useExecutionGraphQL(options);
  } else {
    console.log('[ExecutionProvider] Using WebSocket execution');
    return useExecution(options);
  }
}