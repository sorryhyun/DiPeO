import { useCallback, useRef, useState } from 'react';
import type { FormState, FormConfig, FormFieldUpdate, ValidationError } from '@/domain/diagram/forms/types';

export function useFormState<T extends Record<string, any> = Record<string, any>>(
  config: FormConfig<T>
) {
  const { initialValues, enableReinitialize = false } = config;

  const [formState, setFormState] = useState<FormState<T>>(() => ({
    data: initialValues,
    errors: {},
    touched: {},
    dirty: {},
    isSubmitting: false,
    isValidating: false,
  }));

  const initialValuesRef = useRef(initialValues);

  if (enableReinitialize && initialValuesRef.current !== initialValues) {
    initialValuesRef.current = initialValues;
    setFormState(prev => ({
      ...prev,
      data: initialValues,
      dirty: {},
      touched: {},
      errors: {},
    }));
  }

  const updateField = useCallback((update: FormFieldUpdate) => {
    const { field, value, touch = true } = update;

    setFormState(prev => {
      const isDirty = value !== initialValuesRef.current[field as keyof T];

      return {
        ...prev,
        data: {
          ...prev.data,
          [field]: value,
        },
        dirty: {
          ...prev.dirty,
          [field]: isDirty,
        },
        touched: touch ? {
          ...prev.touched,
          [field]: true,
        } : prev.touched,
      };
    });
  }, []);

  const updateFields = useCallback((updates: Partial<T>) => {
    setFormState(prev => {
      const newDirty = { ...prev.dirty };

      Object.entries(updates).forEach(([field, value]) => {
        newDirty[field] = value !== initialValuesRef.current[field as keyof T];
      });

      return {
        ...prev,
        data: {
          ...prev.data,
          ...updates,
        },
        dirty: newDirty,
      };
    });
  }, []);

  const setFieldError = useCallback((field: string, error: ValidationError | null) => {
    setFormState(prev => {
      const newErrors = { ...prev.errors };

      if (error) {
        newErrors[field] = [error];
      } else {
        delete newErrors[field];
      }

      return {
        ...prev,
        errors: newErrors,
      };
    });
  }, []);

  const setFieldTouched = useCallback((field: string, touched = true) => {
    setFormState(prev => ({
      ...prev,
      touched: {
        ...prev.touched,
        [field]: touched,
      },
    }));
  }, []);

  const setErrors = useCallback((errors: Record<string, ValidationError[]>) => {
    setFormState(prev => ({
      ...prev,
      errors,
    }));
  }, []);

  const setSubmitting = useCallback((isSubmitting: boolean) => {
    setFormState(prev => ({
      ...prev,
      isSubmitting,
    }));
  }, []);

  const setValidating = useCallback((isValidating: boolean) => {
    setFormState(prev => ({
      ...prev,
      isValidating,
    }));
  }, []);

  const reset = useCallback((values?: Partial<T>) => {
    const resetValues = values
      ? { ...initialValuesRef.current, ...values }
      : initialValuesRef.current;

    setFormState({
      data: resetValues,
      errors: {},
      touched: {},
      dirty: {},
      isSubmitting: false,
      isValidating: false,
    });
  }, []);

  const isDirty = Object.values(formState.dirty).some(Boolean);
  const isTouched = Object.values(formState.touched).some(Boolean);
  const hasErrors = Object.keys(formState.errors).length > 0;

  return {
    formState,
    operations: {
      updateField,
      updateFields,
      setFieldError,
      setFieldTouched,
      setErrors,
      setSubmitting,
      setValidating,
      reset,
    },
    computed: {
      isDirty,
      isTouched,
      hasErrors,
    },
  };
}
