import { ApolloClient, InMemoryCache, split } from '@apollo/client';
import { getMainDefinition } from '@apollo/client/utilities';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';
import { createUploadLink } from 'apollo-upload-client';
import { useUnifiedStore } from '@/core/store/unifiedStore';

const httpLink = createUploadLink({
  uri: `http://${import.meta.env.VITE_API_HOST || 'localhost:8000'}/graphql`,
  credentials: 'same-origin',
});

let isConnected = true;

const wsClient = createClient({
  url: `ws://${import.meta.env.VITE_API_HOST || 'localhost:8000'}/graphql`,
  connectionParams: {
  },
  shouldRetry: () => true,
  retryAttempts: Infinity,
  retryWait: async (retryCount) => {
    await new Promise((resolve) =>
      setTimeout(resolve, Math.min(1000 * Math.pow(2, retryCount) + Math.random() * 1000, 30000))
    );
  },
  on: {
    connected: () => {
      isConnected = true;
      console.log('[GraphQL WS] Connected to server');
    },
    closed: () => {
      isConnected = false;
      console.log('[GraphQL WS] Disconnected from server');
      
    },
    error: (error) => {
      console.error('[GraphQL WS] Error:', error);
    },
  },
});

const wsLink = new GraphQLWsLink(wsClient);

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

export const apolloClient = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache({
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
          diagrams: {
            keyArgs: ['filter'],
            merge(existing = [], incoming) {
              return incoming;
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
    possibleTypes: {
      NodeDataUnion: [
        'StartNodeData',
        'PersonJobNodeData',
        'ConditionNodeData',
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
      errorPolicy: 'all',
    },
    query: {
      errorPolicy: 'all',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
});