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
    // Poll for state if not immediately available
    if (!state) {
      const checkInterval = setInterval(() => {
        if (window.oai?.widget?.getState) {
          const currentState = window.oai.widget.getState();
          if (currentState) {
            setState(currentState as T);
            clearInterval(checkInterval);
          }
        }
      }, 100);

      // Stop checking after 5 seconds
      setTimeout(() => clearInterval(checkInterval), 5000);

      return () => clearInterval(checkInterval);
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
