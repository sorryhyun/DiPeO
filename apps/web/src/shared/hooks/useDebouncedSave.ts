import { useRef, useCallback, useEffect } from 'react';

interface UseDebouncedSaveOptions {
  delay?: number;
  onSave: (filename: string) => Promise<void>;
  enabled?: boolean;
}

export function useDebouncedSave(options: UseDebouncedSaveOptions) {
  const { delay = 1000, onSave, enabled = true } = options;
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingSaveRef = useRef<string | null>(null);

  // Clear any pending save on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const debouncedSave = useCallback((filename: string) => {
    if (!enabled) return;

    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Store the pending save
    pendingSaveRef.current = filename;

    // Set up new timeout
    timeoutRef.current = setTimeout(async () => {
      if (pendingSaveRef.current) {
        try {
          await onSave(pendingSaveRef.current);
        } catch (error) {
          console.error('Debounced save failed:', error);
        } finally {
          pendingSaveRef.current = null;
        }
      }
    }, delay);
  }, [delay, onSave, enabled]);

  const cancelPendingSave = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    pendingSaveRef.current = null;
  }, []);

  const saveImmediately = useCallback(async (filename: string) => {
    // Cancel any pending save
    cancelPendingSave();
    
    // Save immediately
    await onSave(filename);
  }, [onSave, cancelPendingSave]);

  return {
    debouncedSave,
    cancelPendingSave,
    saveImmediately,
    hasPendingSave: () => pendingSaveRef.current !== null
  };
}