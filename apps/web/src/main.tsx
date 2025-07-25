import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { ApolloProvider } from '@apollo/client';
import { enableMapSet } from 'immer';
import App from './App';
import './index.css';
import { queryClient } from '@/lib/utils/trpc';
import { apolloClient } from './lib/graphql/client';

// Import generated node registry to register all node types
import '@/features/diagram-editor/config/nodeRegistryGenerated';

// Enable Immer's MapSet plugin before any store initialization
enableMapSet();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ApolloProvider client={apolloClient}>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </ApolloProvider>
  </React.StrictMode>
);