/**
 * Hook to access widget state from OpenAI's widget runtime
 *
 * This hook provides access to the widget's state object that is passed
 * via window.oai.widget.setState() from the MCP server response.
 */

import { useEffect, useState } from 'react';

declare global {
  interface Window {
    oai?: {
      widget?: {
        setState?: (state: any) => void;
        getState?: () => any;
      };
    };
  }
}

/**
 * Hook to get and subscribe to widget state updates
 */
export function useWidgetState<T = any>(): T | null {
  const [state, setState] = useState<T | null>(() => {
    // Try to get initial state
    if (typeof window !== 'undefined' && window.oai?.widget?.getState) {
      return window.oai.widget.getState() as T;
    }
    return null;
  });

  useEffect(() => {
    // Poll for state if not immediately available using exponential backoff
    if (!state) {
      let delay = 100; // Start at 100ms
      const maxDelay = 2000; // Cap at 2 seconds
      const maxAttempts = 10; // Try up to 10 times
      let attempts = 0;
      let timeoutId: NodeJS.Timeout;

      const poll = () => {
        if (window.oai?.widget?.getState) {
          const currentState = window.oai.widget.getState();
          if (currentState) {
            setState(currentState as T);
            return;
          }
        }

        attempts++;
        if (attempts < maxAttempts) {
          delay = Math.min(delay * 1.5, maxDelay);
          timeoutId = setTimeout(poll, delay);
        }
      };

      poll();

      return () => {
        if (timeoutId) clearTimeout(timeoutId);
      };
    }
  }, [state]);

  return state;
}

/**
 * Hook to get widget props from state
 * Alias for useWidgetState for clearer semantics
 */
export function useWidgetProps<T = any>(): T | null {
  return useWidgetState<T>();
}
