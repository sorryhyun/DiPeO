import { useCallback, useLayoutEffect, useRef } from 'react';

/**
 * useEvent - A React hook that provides a stable callback reference
 * 
 * This pattern ensures callbacks always have access to the latest values
 * without causing unnecessary re-renders. It's particularly useful for:
 * - Event handlers with complex dependencies
 * - Callbacks passed to WebSocket or other external systems
 * - Functions that need to access latest state without re-subscribing
 * 
 * Based on the proposed React useEvent RFC:
 * https://github.com/reactjs/rfcs/blob/useevent/text/0000-useevent.md
 * 
 * @param handler - The callback function that may capture changing values
 * @returns A stable callback reference that always calls the latest handler
 */
export function useEvent<T extends (...args: any[]) => any>(handler: T): T {
  const handlerRef = useRef<T>(handler);
  
  // Update the ref to the latest handler on every render
  // Using useLayoutEffect to ensure synchronous updates
  useLayoutEffect(() => {
    handlerRef.current = handler;
  });
  
  // Return a stable callback that calls the latest handler
  return useCallback((...args: Parameters<T>) => {
    const fn = handlerRef.current;
    return fn(...args);
  }, []) as T;
}

/**
 * Type-safe version with explicit parameter and return types
 */
export function useEventTyped<P extends readonly unknown[], R>(
  handler: (...args: P) => R
): (...args: P) => R {
  return useEvent(handler);
}