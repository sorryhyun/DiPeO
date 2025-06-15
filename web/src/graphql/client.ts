import { ApolloClient, InMemoryCache, split, HttpLink } from '@apollo/client';
import { getMainDefinition } from '@apollo/client/utilities';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';

// HTTP link for queries and mutations
const httpLink = new HttpLink({
  uri: `http://${import.meta.env.VITE_API_HOST || 'localhost:8000'}/graphql`,
  credentials: 'include', // Include cookies for authentication if needed
});

// WebSocket link for subscriptions
const wsLink = new GraphQLWsLink(
  createClient({
    url: `ws://${import.meta.env.VITE_API_HOST || 'localhost:8000'}/graphql`,
    connectionParams: {
      // Add authentication params here if needed
    },
    // Auto-reconnect on disconnect
    shouldRetry: () => true,
    retryAttempts: Infinity,
    retryWait: async (retryCount) => {
      // Exponential backoff with jitter
      await new Promise((resolve) =>
        setTimeout(resolve, Math.min(1000 * Math.pow(2, retryCount) + Math.random() * 1000, 30000))
      );
    },
  })
);

// Split link - use WebSocket for subscriptions, HTTP for everything else
const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink
);

// Create Apollo Client instance
export const apolloClient = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache({
    // Configure cache for DiPeO types
    typePolicies: {
      Diagram: {
        keyFields: ['metadata', ['id']],
      },
      Node: {
        keyFields: ['id'],
      },
      Person: {
        keyFields: ['id'],
      },
      ApiKey: {
        keyFields: ['id'],
      },
      ExecutionState: {
        keyFields: ['id'],
      },
      Query: {
        fields: {
          // Merge paginated results
          diagrams: {
            keyArgs: ['filter'],
            merge(existing = [], incoming) {
              return [...existing, ...incoming];
            },
          },
          executions: {
            keyArgs: ['filter'],
            merge(existing = [], incoming) {
              return [...existing, ...incoming];
            },
          },
        },
      },
    },
    // Enable possibleTypes for union types
    possibleTypes: {
      NodeDataUnion: [
        'StartNodeData',
        'PersonJobNodeData',
        'ConditionNodeData',
        'JobNodeData',
        'EndpointNodeData',
        'DBNodeData',
        'UserResponseNodeData',
        'NotionNodeData',
        'PersonBatchJobNodeData',
      ],
      DiagramOperationResult: ['Diagram', 'OperationError'],
      ExecutionOperationResult: ['ExecutionState', 'OperationError'],
    },
  }),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
    },
    query: {
      errorPolicy: 'all',
    },
  },
});