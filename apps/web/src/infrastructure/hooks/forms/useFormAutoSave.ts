import { useCallback, useEffect, useRef, useState } from 'react';
import type { FormAutoSaveConfig, FormState } from '@/domain/diagram/forms/types';

interface UseFormAutoSaveOptions<T extends Record<string, any>> {
  config: FormAutoSaveConfig;
  formState: FormState<T>;
  hasErrors: boolean;
}

export function useFormAutoSave<T extends Record<string, any>>({
  config,
  formState,
  hasErrors,
}: UseFormAutoSaveOptions<T>) {
  const { enabled, delay = 1000, onSave, fields } = config;
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [saveError, setSaveError] = useState<Error | null>(null);
  
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const lastSavedDataRef = useRef<T>(formState.data);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const save = useCallback(async () => {
    if (!enabled || hasErrors || isSaving) {
      return;
    }

    const dataToSave = fields
      ? Object.fromEntries(
          fields.map(field => [field, formState.data[field]])
        ) as Partial<T>
      : formState.data;

    const hasChanges = JSON.stringify(dataToSave) !== JSON.stringify(
      fields
        ? Object.fromEntries(
            fields.map(field => [field, lastSavedDataRef.current[field]])
          )
        : lastSavedDataRef.current
    );

    if (!hasChanges) {
      return;
    }

    try {
      setIsSaving(true);
      setSaveError(null);
      
      await onSave(dataToSave);
      
      if (mountedRef.current) {
        lastSavedDataRef.current = formState.data;
        setLastSaved(new Date());
      }
    } catch (error) {
      if (mountedRef.current) {
        setSaveError(error instanceof Error ? error : new Error('Save failed'));
      }
    } finally {
      if (mountedRef.current) {
        setIsSaving(false);
      }
    }
  }, [enabled, hasErrors, isSaving, onSave, fields, formState.data]);

  const scheduleSave = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    if (!enabled || hasErrors) {
      return;
    }

    timeoutRef.current = setTimeout(() => {
      void save();
    }, delay);
  }, [enabled, hasErrors, delay, save]);

  useEffect(() => {
    const isDirty = Object.values(formState.dirty).some(Boolean);
    
    if (enabled && isDirty && !hasErrors && !formState.isSubmitting) {
      scheduleSave();
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [formState.data, formState.dirty, formState.isSubmitting, hasErrors, enabled, scheduleSave]);

  const forceSave = useCallback(async () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    await save();
  }, [save]);

  const resetAutoSave = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    lastSavedDataRef.current = formState.data;
    setSaveError(null);
  }, [formState.data]);

  return {
    isSaving,
    lastSaved,
    saveError,
    forceSave,
    resetAutoSave,
  };
}