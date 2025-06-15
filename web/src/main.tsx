import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { ApolloProvider } from '@apollo/client';
import { enableMapSet } from 'immer';
import App from './App';
import './index.css';
import { queryClient } from './utils/trpc';
import { apolloClient } from './graphql/client';

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