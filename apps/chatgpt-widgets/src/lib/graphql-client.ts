/**
 * GraphQL client for DiPeO widgets
 *
 * Provides a simple interface to query the DiPeO GraphQL API from widgets.
 * The endpoint URL is configurable via environment variable or defaults to localhost.
 */

const GRAPHQL_ENDPOINT = import.meta.env.VITE_DIPEO_GRAPHQL_URL || 'http://localhost:8000/graphql';

export interface GraphQLResponse<T = any> {
  data?: T;
  errors?: Array<{
    message: string;
    locations?: Array<{ line: number; column: number }>;
    path?: Array<string | number>;
  }>;
}

/**
 * Execute a GraphQL query against the DiPeO server
 */
export async function queryGraphQL<T = any>(
  query: string,
  variables?: Record<string, any>
): Promise<GraphQLResponse<T>> {
  try {
    const response = await fetch(GRAPHQL_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, variables }),
    });

    if (!response.ok) {
      // Try to parse error body for more details
      let errorMessage = `GraphQL request failed: ${response.status} ${response.statusText}`;
      try {
        const errorBody = await response.json();
        if (errorBody.errors?.[0]?.message) {
          errorMessage = errorBody.errors[0].message;
        }
      } catch {
        // Ignore JSON parse errors, use default message
      }
      throw new Error(errorMessage);
    }

    return response.json();
  } catch (error) {
    // Handle network errors (timeout, connection refused, etc.)
    if (error instanceof Error) {
      // Re-throw with more context if it's a network error
      if (error.message.includes('fetch')) {
        throw new Error(`Network error: Unable to reach DiPeO server at ${GRAPHQL_ENDPOINT}`);
      }
      throw error;
    }
    throw new Error('Unknown error occurred while querying GraphQL');
  }
}
