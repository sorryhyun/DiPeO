import { ApolloCache, DocumentNode, OperationVariables } from '@apollo/client';


/**
 * Common refetch queries configuration
 */
export interface RefetchConfig<TVariables = OperationVariables> {
  queries: Array<{
    query: DocumentNode;
    variables?: TVariables;
  }>;
}

export function createRefetchQueries<TVariables = OperationVariables>(config: RefetchConfig<TVariables>) {
  return config.queries.map(({ query, variables }) => ({
    query,
    variables: variables || {}
  }));
}