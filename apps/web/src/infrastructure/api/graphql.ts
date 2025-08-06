/**
 * GraphQL API service - uses generated GraphQL operations
 * Provides a unified interface to all GraphQL functionality
 */

import { apolloClient } from '@/lib/graphql/client';
import * as GraphQLOperations from '@/__generated__/graphql';
import type { OperationVariables } from '@apollo/client';

/**
 * Centralized GraphQL service that leverages generated hooks and operations
 * All actual queries are defined in __generated__/queries/*.graphql and generated
 */
export class GraphQLService {
  /**
   * Direct access to Apollo Client for advanced use cases
   */
  static get client() {
    return apolloClient;
  }
  
  /**
   * Use generated query hooks
   * Example: GraphQLService.hooks.useGetDiagramQuery
   */
  static get hooks() {
    return GraphQLOperations;
  }
  
  /**
   * Execute a query directly (for non-hook usage)
   */
  static async query<TData = any, TVariables extends OperationVariables = OperationVariables>(
    query: any,
    variables?: TVariables,
  ): Promise<TData> {
    const result = await this.client.query({
      query,
      variables,
      fetchPolicy: 'cache-first',
    });
    return result.data;
  }
  
  /**
   * Execute a mutation
   */
  static async mutate<TData = any, TVariables extends OperationVariables = OperationVariables>(
    mutation: any,
    variables?: TVariables,
  ): Promise<TData> {
    const result = await this.client.mutate({
      mutation,
      variables,
    });
    return result.data;
  }
  
  /**
   * Subscribe to real-time updates
   */
  static subscribe<TData = any, TVariables extends OperationVariables = OperationVariables>(
    subscription: any,
    variables?: TVariables,
  ) {
    return this.client.subscribe({
      query: subscription,
      variables,
    });
  }
  
  /**
   * Clear Apollo cache
   */
  static clearCache() {
    return this.client.clearStore();
  }
  
  /**
   * Reset Apollo cache and refetch active queries
   */
  static async resetCache() {
    return this.client.resetStore();
  }
}