/**
 * Executor module exports
 */

// Base executor classes and interfaces
export {
  BaseExecutor,
  ClientSafeExecutor,
  ServerOnlyExecutor,
  BaseExecutorFactory,
  ExecutorNotFoundError,
  UnsupportedEnvironmentError
} from './base-executor';
export type { ExecutorFactory } from './base-executor';

// Import ExecutorFactory type for use in this file
import type { ExecutorFactory } from './base-executor';

// Client-safe executors
export {
  StartExecutor,
  ConditionExecutor,
  JobExecutor,
  EndpointExecutor
} from './client-safe-executors';

// Server-only executors
export {
  PersonJobExecutor,
  PersonBatchJobExecutor,
  DBExecutor,
  UnsupportedServerExecutor
} from './server-only-executors';

// Factory implementations
export { ClientExecutorFactory } from './client-executor-factory';
export { ServerExecutorFactory } from './server-executor-factory';

// Convenience function to create appropriate factory based on environment
export function createExecutorFactory(environment?: 'client' | 'server'): ExecutorFactory {
  // Import the factories here to avoid circular dependencies
  const { ClientExecutorFactory } = require('./client-executor-factory');
  const { ServerExecutorFactory } = require('./server-executor-factory');
  
  // Detect environment if not specified
  const env = environment || detectEnvironment();
  
  switch (env) {
    case 'client':
      return new ClientExecutorFactory();
    case 'server':
      return new ServerExecutorFactory();
    default:
      throw new Error(`Unsupported environment: ${env}`);
  }
}

/**
 * Detect the current execution environment
 */
function detectEnvironment(): 'client' | 'server' {
  // Check if we're in a browser environment
  if (typeof window !== 'undefined' && typeof document !== 'undefined') {
    return 'client';
  }
  
  // Check if we're in a Node.js environment
  if (typeof global !== 'undefined' && typeof process !== 'undefined') {
    return 'server';
  }
  
  // Default to client for safety (more restrictive)
  return 'client';
}

/**
 * Get execution capabilities for the current environment
 */
export function getExecutionCapabilities(environment?: 'client' | 'server') {
  const factory = createExecutorFactory(environment);
  
  if ('getExecutionCapabilities' in factory) {
    return (factory as any).getExecutionCapabilities();
  }
  
  return {
    clientSafe: [],
    serverOnly: [],
    supported: factory.getSupportedNodeTypes()
  };
}