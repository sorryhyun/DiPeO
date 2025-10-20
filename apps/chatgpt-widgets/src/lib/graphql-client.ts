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
  const response = await fetch(GRAPHQL_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, variables }),
  });

  if (!response.ok) {
    throw new Error(`GraphQL request failed: ${response.statusText}`);
  }

  return response.json();
}
