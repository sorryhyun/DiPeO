import { useCallback, useRef } from 'react';
import type { FieldValidator, ValidationResult, ValidationError, FormState } from '@/domain/diagram/forms/types';

interface UseFormValidationOptions {
  validators?: Record<string, FieldValidator>;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  formState: FormState;
  setFieldError: (field: string, error: ValidationError | null) => void;
  setErrors: (errors: Record<string, ValidationError[]>) => void;
  setValidating: (isValidating: boolean) => void;
}

export function useFormValidation({
  validators = {},
  validateOnChange = true,
  validateOnBlur = true,
  formState,
  setFieldError,
  setErrors,
  setValidating,
}: UseFormValidationOptions) {
  const validatorsRef = useRef(validators);
  validatorsRef.current = validators;

  const validateField = useCallback(async (
    field: string,
    value?: any
  ): Promise<ValidationResult> => {
    const validator = validatorsRef.current[field];
    
    if (!validator) {
      return { valid: true, errors: [] };
    }

    const fieldValue = value ?? formState.data[field];
    
    try {
      setValidating(true);
      const result = await validator(fieldValue, formState.data);
      
      if (!result.valid && result.errors.length > 0) {
        setFieldError(field, result.errors[0] || null);
      } else {
        setFieldError(field, null);
      }
      
      return result;
    } catch (error) {
      const validationError: ValidationError = {
        field,
        message: error instanceof Error ? error.message : 'Validation failed',
      };
      
      setFieldError(field, validationError);
      
      return {
        valid: false,
        errors: [validationError],
      };
    } finally {
      setValidating(false);
    }
  }, [formState.data, setFieldError, setValidating]);

  const validateForm = useCallback(async (): Promise<ValidationResult> => {
    const errors: Record<string, ValidationError[]> = {};
    const allErrors: ValidationError[] = [];
    let isValid = true;

    try {
      setValidating(true);
      
      const validationPromises = Object.entries(validatorsRef.current).map(
        async ([field, validator]) => {
          try {
            const result = await validator(formState.data[field], formState.data);
            
            if (!result.valid && result.errors.length > 0) {
              errors[field] = result.errors;
              allErrors.push(...result.errors);
              isValid = false;
            }
          } catch (error) {
            const validationError: ValidationError = {
              field,
              message: error instanceof Error ? error.message : 'Validation failed',
            };
            
            errors[field] = [validationError];
            allErrors.push(validationError);
            isValid = false;
          }
        }
      );

      await Promise.all(validationPromises);
      setErrors(errors);

      return {
        valid: isValid,
        errors: allErrors,
      };
    } finally {
      setValidating(false);
    }
  }, [formState.data, setErrors, setValidating]);

  const clearFieldError = useCallback((field: string) => {
    setFieldError(field, null);
  }, [setFieldError]);

  const clearAllErrors = useCallback(() => {
    setErrors({});
  }, [setErrors]);

  const shouldValidateOnChange = useCallback((field: string) => {
    return validateOnChange && formState.touched[field];
  }, [validateOnChange, formState.touched]);

  const shouldValidateOnBlur = useCallback(() => {
    return validateOnBlur;
  }, [validateOnBlur]);

  return {
    validateField,
    validateForm,
    clearFieldError,
    clearAllErrors,
    shouldValidateOnChange,
    shouldValidateOnBlur,
  };
}