import React from 'react';
import { QueryClient } from '@tanstack/react-query';
import { API_BASE_URL } from './apiConfig';

// Simple tRPC-style client for now
// Will be enhanced when backend tRPC is fully configured

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

// Placeholder for tRPC hooks
export const trpc = {
  Provider: ({ children }: { children: React.ReactNode }) => children,
  diagram: {
    execute: {
      useMutation: () => ({
        mutateAsync: async (input: any) => {
          const response = await fetch(`${API_BASE_URL}/trpc/diagram.execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input })
          });
          const data = await response.json();
          return data.result?.data;
        }
      })
    }
  }
};

export function createTRPCClient() {
  return {} as any;
}