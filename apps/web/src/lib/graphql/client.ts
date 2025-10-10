import { ApolloClient, InMemoryCache, split } from '@apollo/client';
import { getMainDefinition } from '@apollo/client/utilities';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';
import { createUploadLink } from 'apollo-upload-client';
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';
import { toast } from 'sonner';

// Event emitter for WebSocket lifecycle events
type WSLifecycleListener = (event: { type: 'shutdown' | 'reconnected' }) => void;
const wsLifecycleListeners = new Set<WSLifecycleListener>();

export const addWSLifecycleListener = (listener: WSLifecycleListener) => {
  wsLifecycleListeners.add(listener);
  return () => wsLifecycleListeners.delete(listener);
};

const notifyWSLifecycle = (event: { type: 'shutdown' | 'reconnected' }) => {
  wsLifecycleListeners.forEach(listener => listener(event));
};

const httpLink = createUploadLink({
  uri: `http://${import.meta.env.VITE_API_HOST || 'localhost:8000'}/graphql`,
  credentials: 'same-origin',
});

let isConnected = true;
let retryCount = 0;
let lastConnectionTime = Date.now();
let shouldStopRetrying = false;

const wsClient = createClient({
  url: `ws://${import.meta.env.VITE_API_HOST || 'localhost:8000'}/graphql`,
  connectionParams: {
  },
  shouldRetry: () => !shouldStopRetrying,
  retryAttempts: Infinity,
  retryWait: async (retryCount) => {
    const waitTime = Math.min(1000 * Math.pow(2, retryCount) + Math.random() * 1000, 30000);
    console.log(`[GraphQL WS] Retrying connection in ${Math.round(waitTime / 1000)}s (attempt ${retryCount + 1})`);
    await new Promise((resolve) => setTimeout(resolve, waitTime));
  },
  on: {
    connected: () => {
      const wasDisconnected = !isConnected;
      isConnected = true;
      lastConnectionTime = Date.now();
      shouldStopRetrying = false;

      if (wasDisconnected && retryCount > 0) {
        console.log(`[GraphQL WS] Reconnected to server after ${retryCount} attempts`);
        toast.success('WebSocket reconnected');
      } else {
        console.log('[GraphQL WS] Connected to server');
      }
      retryCount = 0;
    },
    closed: (event) => {
      const wasConnected = isConnected;
      isConnected = false;
      retryCount++;

      const connectionDuration = Date.now() - lastConnectionTime;
      const reason = event instanceof CloseEvent ?
        `Code: ${event.code}, Reason: ${event.reason || 'No reason provided'}` :
        'Unknown reason';

      console.log(`[GraphQL WS] Connection closed - ${reason}`);
      console.log(`[GraphQL WS] Connection was active for ${Math.round(connectionDuration / 1000)}s`);

      if (wasConnected) {
        if (event instanceof CloseEvent) {
          if (event.code === 1000) {
            console.log('[GraphQL WS] Normal closure - server shutdown gracefully');
            shouldStopRetrying = true;
            toast.info('Server stopped - monitoring session ended');
            notifyWSLifecycle({ type: 'shutdown' });
          } else if (event.code === 1001) {
            console.log('[GraphQL WS] Server going away - likely CLI execution finished');
            shouldStopRetrying = true;
            toast.info('CLI execution finished - server stopped');
            notifyWSLifecycle({ type: 'shutdown' });
          } else if (event.code === 1006) {
            console.log('[GraphQL WS] Abnormal closure (network error or timeout)');
            toast.error('WebSocket connection lost - Attempting to reconnect...');
          } else {
            toast.warning(`WebSocket closed: ${reason}`);
          }
        } else {
          toast.warning('WebSocket connection closed');
        }
      }
    },
    error: (error) => {
      console.error('[GraphQL WS] Error:', error);
      if (error instanceof Error) {
        console.error('[GraphQL WS] Error details:', error.message, error.stack);
      }
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

// Export connection status for components to use
export const getConnectionStatus = () => ({
  isConnected,
  retryCount,
  lastConnectionTime,
  shouldStopRetrying
});

// Allow components to manually reconnect (resets the stop flag)
export const resetConnectionRetry = () => {
  console.log('[GraphQL WS] Manually resetting connection retry flag');
  shouldStopRetrying = false;
  wsClient.dispose();
};

// Add ping/pong keep-alive to detect timeouts faster
setInterval(() => {
  if (isConnected && wsClient) {
    // The graphql-ws client handles ping/pong internally
    // This is just to log connection health periodically
    const connectionAge = Date.now() - lastConnectionTime;
    if (connectionAge > 60000) { // Log every minute
      console.log(`[GraphQL WS] Connection healthy - Active for ${Math.round(connectionAge / 1000)}s`);
      lastConnectionTime = Date.now(); // Reset to avoid spamming logs
    }
  }
}, 30000); // Check every 30 seconds

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
