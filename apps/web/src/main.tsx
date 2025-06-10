import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { enableMapSet } from 'immer';
import App from './App';
import './index.css';
import { queryClient } from './utils/trpc';

// Enable Immer's MapSet plugin before any store initialization
enableMapSet();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);