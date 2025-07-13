import { useRef, useCallback } from 'react';

/**
 * Returns a stable callback that always calls the latest version of the provided function.
 * This prevents unnecessary re-renders when passing callbacks to child components.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function useEvent<T extends (...args: any[]) => any>(fn: T): T {
  const ref = useRef(fn);
  ref.current = fn;

  return useCallback((...args: Parameters<T>) => {
    return ref.current(...args);
  }, []) as T;
}