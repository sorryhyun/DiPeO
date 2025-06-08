import { useState, useCallback, useMemo } from 'react';
import { z } from 'zod';
import { ValidationError, extractFieldErrors, createUserMessage } from './errors';

/**
 * Validation hook for forms
 */
export function useValidation<T>(schema: z.ZodSchema<T>) {
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);

  const validate = useCallback((data: unknown): T | null => {
    try {
      const result = schema.parse(data);
      setErrors({});
      setGeneralError(null);
      return result;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors = extractFieldErrors(error);
        setErrors(fieldErrors);
        setGeneralError(createUserMessage(error));
      } else {
        setGeneralError('Validation failed');
      }
      return null;
    }
  }, [schema]);

  const validateField = useCallback((field: string, value: unknown): boolean => {
    try {
      // Create a partial schema for single field validation
      const fieldSchema = schema.shape?.[field];
      if (fieldSchema) {
        fieldSchema.parse(value);
        setErrors(prev => {
          const next = { ...prev };
          delete next[field];
          return next;
        });
        return true;
      }
      return false;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const message = createUserMessage(error);
        setErrors(prev => ({ ...prev, [field]: message }));
      }
      return false;
    }
  }, [schema]);

  const clearErrors = useCallback(() => {
    setErrors({});
    setGeneralError(null);
  }, []);

  const clearFieldError = useCallback((field: string) => {
    setErrors(prev => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }, []);

  return {
    validate,
    validateField,
    errors,
    generalError,
    clearErrors,
    clearFieldError,
    hasErrors: Object.keys(errors).length > 0 || generalError !== null
  };
}

/**
 * Async validation hook with loading state
 */
export function useAsyncValidation<T>(
  schema: z.ZodSchema<T>,
  asyncValidator?: (data: T) => Promise<void>
) {
  const [isValidating, setIsValidating] = useState(false);
  const baseValidation = useValidation(schema);

  const validateAsync = useCallback(async (data: unknown): Promise<T | null> => {
    // First do synchronous validation
    const result = baseValidation.validate(data);
    if (!result) {
      return null;
    }

    // Then do async validation if provided
    if (asyncValidator) {
      setIsValidating(true);
      try {
        await asyncValidator(result);
        return result;
      } catch (error) {
        if (error instanceof ValidationError) {
          baseValidation.errors[error.field || 'general'] = error.message;
        } else {
          baseValidation.generalError = 'Async validation failed';
        }
        return null;
      } finally {
        setIsValidating(false);
      }
    }

    return result;
  }, [schema, asyncValidator, baseValidation]);

  return {
    ...baseValidation,
    validateAsync,
    isValidating
  };
}

/**
 * Field-level validation hook
 */
export function useFieldValidation<T>(
  name: string,
  schema: z.ZodSchema<T>,
  value: T,
  onChange: (value: T) => void
) {
  const [error, setError] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);

  const handleChange = useCallback((newValue: T) => {
    onChange(newValue);
    
    if (touched) {
      try {
        schema.parse(newValue);
        setError(null);
      } catch (err) {
        if (err instanceof z.ZodError) {
          setError(createUserMessage(err));
        }
      }
    }
  }, [onChange, schema, touched]);

  const handleBlur = useCallback(() => {
    setTouched(true);
    try {
      schema.parse(value);
      setError(null);
    } catch (err) {
      if (err instanceof z.ZodError) {
        setError(createUserMessage(err));
      }
    }
  }, [value, schema]);

  return {
    value,
    error: touched ? error : null,
    onChange: handleChange,
    onBlur: handleBlur,
    touched
  };
}