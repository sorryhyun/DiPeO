import { useState, useCallback, useRef, useEffect, type FormEvent } from 'react';
import { z, ZodSchema } from 'zod';
import { toast } from 'sonner';

export type FormState<T> = {
  values: T;
  errors: Record<string, string[]>;
  touched: Record<string, boolean>;
  dirty: Record<string, boolean>;
  isSubmitting: boolean;
  isValidating: boolean;
  submitCount: number;
  isValid: boolean;
};

export type FormConfig<T> = {
  initialValues: T;
  validationSchema?: ZodSchema<T>;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  validateOnSubmit?: boolean;
  enableReinitialize?: boolean;
  autoSave?: boolean;
  autoSaveDelay?: number;
  showToasts?: boolean;
  onSubmit?: (values: T) => void | Promise<void>;
  onValidate?: (values: T) => Record<string, string[]> | Promise<Record<string, string[]>>;
  onChange?: (values: T, field?: keyof T) => void;
  onReset?: () => void;
};

export type FieldHelpers<T> = {
  value: any;
  error: string | undefined;
  touched: boolean;
  dirty: boolean;

  onChange: (value: any) => void;
  onBlur: () => void;
  setError: (error: string | null) => void;
  setTouched: (touched: boolean) => void;
};

export type UseFormReturn<T> = {
  values: T;
  errors: Record<string, string[]>;
  touched: Record<string, boolean>;
  dirty: Record<string, boolean>;

  isSubmitting: boolean;
  isValidating: boolean;
  isValid: boolean;
  isDirty: boolean;
  isTouched: boolean;
  submitCount: number;

  getFieldProps: <K extends keyof T>(field: K) => {
    name: K;
    value: T[K];
    onChange: (e: any) => void;
    onBlur: () => void;
    error: string | undefined;
  };

  getFieldHelpers: <K extends keyof T>(field: K) => FieldHelpers<T>;

  setFieldValue: <K extends keyof T>(field: K, value: T[K]) => void;
  setFieldError: (field: keyof T, error: string | string[] | null) => void;
  setFieldTouched: (field: keyof T, touched?: boolean) => void;
  setValues: (values: Partial<T>) => void;
  setErrors: (errors: Record<string, string[]>) => void;

  validateField: <K extends keyof T>(field: K) => Promise<boolean>;
  validateForm: () => Promise<boolean>;

  handleSubmit: (e?: FormEvent) => Promise<void>;
  handleReset: () => void;

  resetForm: (values?: Partial<T>) => void;
  clearErrors: () => void;
  clearField: <K extends keyof T>(field: K) => void;
};

const DEFAULT_CONFIG = {
  validateOnChange: true,
  validateOnBlur: true,
  validateOnSubmit: true,
  enableReinitialize: false,
  autoSave: false,
  autoSaveDelay: 1000,
  showToasts: false,
};

export function useForm<T extends Record<string, any>>(
  config: FormConfig<T>
): UseFormReturn<T> {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };
  const {
    initialValues,
    validationSchema,
    validateOnChange,
    validateOnBlur,
    validateOnSubmit,
    enableReinitialize,
    autoSave,
    autoSaveDelay,
    showToasts,
    onSubmit,
    onValidate,
    onChange,
    onReset,
  } = mergedConfig;

  const [state, setState] = useState<FormState<T>>({
    values: initialValues,
    errors: {},
    touched: {},
    dirty: {},
    isSubmitting: false,
    isValidating: false,
    submitCount: 0,
    isValid: true,
  });

  const initialValuesRef = useRef(initialValues);
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const isMountedRef = useRef(true);

  if (enableReinitialize && initialValuesRef.current !== initialValues) {
    initialValuesRef.current = initialValues;
    setState(prev => ({
      ...prev,
      values: initialValues,
      dirty: {},
      touched: {},
      errors: {},
    }));
  }

  const isDirty = Object.values(state.dirty).some(Boolean);
  const isTouched = Object.values(state.touched).some(Boolean);

  const validateWithSchema = useCallback(async (
    values: T,
    field?: keyof T
  ): Promise<Record<string, string[]>> => {
    if (!validationSchema) return {};

    try {
      if (field) {
        // For field-level validation, validate the whole object but only check the specific field
        await validationSchema.parseAsync(values);
        return {};
      } else {
        await validationSchema.parseAsync(values);
        return {};
      }
    } catch (error) {
      if (error instanceof z.ZodError) {
        const errors: Record<string, string[]> = {};
        error.errors.forEach(err => {
          const path = err.path.join('.');
          if (!field || path === String(field)) {
            if (!errors[path]) errors[path] = [];
            errors[path].push(err.message);
          }
        });
        return errors;
      }
      return {};
    }
  }, [validationSchema]);

  const validateWithCustom = useCallback(async (
    values: T
  ): Promise<Record<string, string[]>> => {
    if (!onValidate) return {};

    try {
      const errors = await onValidate(values);
      return errors || {};
    } catch (error) {
      console.error('Custom validation failed:', error);
      return {};
    }
  }, [onValidate]);

  const validateField = useCallback(async <K extends keyof T>(
    field: K
  ): Promise<boolean> => {
    if (!isMountedRef.current) return true;

    setState(prev => ({ ...prev, isValidating: true }));

    const schemaErrors = await validateWithSchema(state.values, field);
    const customErrors = await validateWithCustom(state.values);

    const fieldError = schemaErrors[String(field)] || customErrors[String(field)];

    setState(prev => {
      const newErrors = { ...prev.errors };
      if (fieldError && fieldError.length > 0) {
        newErrors[String(field)] = fieldError;
      } else {
        delete newErrors[String(field)];
      }

      return {
        ...prev,
        errors: newErrors,
        isValidating: false,
        isValid: Object.keys(newErrors).length === 0,
      };
    });

    return !fieldError || fieldError.length === 0;
  }, [state.values, validateWithSchema, validateWithCustom]);

  const validateForm = useCallback(async (): Promise<boolean> => {
    if (!isMountedRef.current) return true;

    setState(prev => ({ ...prev, isValidating: true }));

    const schemaErrors = await validateWithSchema(state.values);
    const customErrors = await validateWithCustom(state.values);

    const allErrors = { ...schemaErrors, ...customErrors };

    setState(prev => ({
      ...prev,
      errors: allErrors,
      isValidating: false,
      isValid: Object.keys(allErrors).length === 0,
    }));

    return Object.keys(allErrors).length === 0;
  }, [state.values, validateWithSchema, validateWithCustom]);

  const setFieldValue = useCallback(<K extends keyof T>(
    field: K,
    value: T[K]
  ) => {
    setState(prev => {
      const isDirty = value !== initialValuesRef.current[field];

      const newValues = {
        ...prev.values,
        [field]: value,
      };

      onChange?.(newValues, field);

      return {
        ...prev,
        values: newValues,
        dirty: {
          ...prev.dirty,
          [field]: isDirty,
        },
      };
    });

    if (validateOnChange) {
      void validateField(field);
    }

    if (autoSave) {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
      autoSaveTimerRef.current = setTimeout(() => {
        if (onSubmit && isMountedRef.current) {
          void onSubmit(state.values);
        }
      }, autoSaveDelay);
    }
  }, [validateOnChange, validateField, autoSave, autoSaveDelay, onSubmit, onChange, state.values]);

  const setFieldError = useCallback((
    field: keyof T,
    error: string | string[] | null
  ) => {
    setState(prev => {
      const newErrors = { ...prev.errors };

      if (error) {
        newErrors[String(field)] = Array.isArray(error) ? error : [error];
      } else {
        delete newErrors[String(field)];
      }

      return {
        ...prev,
        errors: newErrors,
        isValid: Object.keys(newErrors).length === 0,
      };
    });
  }, []);

  const setFieldTouched = useCallback((
    field: keyof T,
    touched = true
  ) => {
    setState(prev => ({
      ...prev,
      touched: {
        ...prev.touched,
        [field]: touched,
      },
    }));

    if (validateOnBlur && touched) {
      void validateField(field);
    }
  }, [validateOnBlur, validateField]);

  const setValues = useCallback((values: Partial<T>) => {
    setState(prev => {
      const newValues = { ...prev.values, ...values };
      const newDirty = { ...prev.dirty };

      Object.keys(values).forEach(field => {
        newDirty[field] = values[field as keyof T] !== initialValuesRef.current[field as keyof T];
      });

      onChange?.(newValues);

      return {
        ...prev,
        values: newValues,
        dirty: newDirty,
      };
    });

    if (validateOnChange) {
      void validateForm();
    }
  }, [validateOnChange, validateForm, onChange]);

  const setErrors = useCallback((errors: Record<string, string[]>) => {
    setState(prev => ({
      ...prev,
      errors,
      isValid: Object.keys(errors).length === 0,
    }));
  }, []);

  const handleSubmit = useCallback(async (e?: FormEvent) => {
    e?.preventDefault();

    if (!onSubmit || state.isSubmitting) return;

    setState(prev => ({
      ...prev,
      isSubmitting: true,
      submitCount: prev.submitCount + 1,
    }));

    let isValid = true;
    if (validateOnSubmit) {
      isValid = await validateForm();
    }

    if (isValid) {
      try {
        await onSubmit(state.values);
        if (showToasts) {
          toast.success('Form submitted successfully');
        }
      } catch (error) {
        if (showToasts) {
          toast.error(error instanceof Error ? error.message : 'Form submission failed');
        }
        console.error('Form submission error:', error);
      }
    } else if (showToasts) {
      toast.error('Please fix the errors before submitting');
    }

    setState(prev => ({
      ...prev,
      isSubmitting: false,
    }));
  }, [onSubmit, state.isSubmitting, state.values, validateOnSubmit, validateForm, showToasts]);

  const handleReset = useCallback(() => {
    setState({
      values: initialValuesRef.current,
      errors: {},
      touched: {},
      dirty: {},
      isSubmitting: false,
      isValidating: false,
      submitCount: 0,
      isValid: true,
    });
    onReset?.();
  }, [onReset]);

  const resetForm = useCallback((values?: Partial<T>) => {
    const resetValues = values
      ? { ...initialValuesRef.current, ...values }
      : initialValuesRef.current;

    setState({
      values: resetValues,
      errors: {},
      touched: {},
      dirty: {},
      isSubmitting: false,
      isValidating: false,
      submitCount: 0,
      isValid: true,
    });
  }, []);

  const clearErrors = useCallback(() => {
    setState(prev => ({
      ...prev,
      errors: {},
      isValid: true,
    }));
  }, []);

  const clearField = useCallback(<K extends keyof T>(field: K) => {
    setState(prev => {
      const newErrors = { ...prev.errors };
      delete newErrors[String(field)];

      return {
        ...prev,
        values: {
          ...prev.values,
          [field]: initialValuesRef.current[field],
        },
        errors: newErrors,
        touched: {
          ...prev.touched,
          [field]: false,
        },
        dirty: {
          ...prev.dirty,
          [field]: false,
        },
        isValid: Object.keys(newErrors).length === 0,
      };
    });
  }, []);

  const getFieldProps = useCallback(<K extends keyof T>(field: K) => {
    const fieldString = String(field);
    const error = state.errors[fieldString]?.[0];

    return {
      name: field,
      value: state.values[field],
      onChange: (e: any) => {
        const value = e?.target?.value !== undefined ? e.target.value : e;
        setFieldValue(field, value);
      },
      onBlur: () => setFieldTouched(field),
      error,
    };
  }, [state.values, state.errors, setFieldValue, setFieldTouched]);

  const getFieldHelpers = useCallback(<K extends keyof T>(field: K): FieldHelpers<T> => {
    const fieldString = String(field);

    return {
      value: state.values[field],
      error: state.errors[fieldString]?.[0],
      touched: state.touched[fieldString] || false,
      dirty: state.dirty[fieldString] || false,

      onChange: (value: any) => setFieldValue(field, value),
      onBlur: () => setFieldTouched(field),
      setError: (error: string | null) => setFieldError(field, error),
      setTouched: (touched: boolean) => setFieldTouched(field, touched),
    };
  }, [state, setFieldValue, setFieldTouched, setFieldError]);

  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, []);

  return {
    values: state.values,
    errors: state.errors,
    touched: state.touched,
    dirty: state.dirty,

    isSubmitting: state.isSubmitting,
    isValidating: state.isValidating,
    isValid: state.isValid,
    isDirty,
    isTouched,
    submitCount: state.submitCount,

    getFieldProps,
    getFieldHelpers,

    setFieldValue,
    setFieldError,
    setFieldTouched,
    setValues,
    setErrors,

    validateField,
    validateForm,

    handleSubmit,
    handleReset,

    resetForm,
    clearErrors,
    clearField,
  };
}
