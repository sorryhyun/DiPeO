/**
 * GraphQL Query Factory Pattern
 * 
 * This module provides factory functions for creating standardized GraphQL operations
 * with consistent error handling, caching strategies, and response patterns.
 * 
 * Benefits:
 * - Reduces boilerplate code from ~150 LOC to ~40 LOC per entity
 * - Standardizes error handling with toast notifications
 * - Provides consistent caching strategies
 * - Simplifies response handling for standard success/error patterns
 * 
 * Usage Example:
 * ```typescript
 * const useDiagramOperations = createEntityOperations({
 *   entityName: 'Diagram',
 *   queries: {
 *     get: {
 *       document: GetDiagramDocument,
 *       cacheStrategy: 'cache-first',
 *       errorMessage: (error) => `Failed to load diagram: ${error.message}`
 *     },
 *     list: {
 *       document: ListDiagramsDocument,
 *       cacheStrategy: 'cache-and-network'
 *     }
 *   },
 *   mutations: {
 *     create: {
 *       document: CreateDiagramDocument,
 *       successMessage: (data) => `Created diagram "${data.create_diagram.diagram?.metadata.name}"`,
 *       options: {
 *         refetchQueries: [{ query: ListDiagramsDocument }]
 *       }
 *     }
 *   }
 * });
 * ```
 */

export * from './factory';
export * from './cacheStrategies';
export * from './responseHandlers';