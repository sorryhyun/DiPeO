import { useCallback, useMemo } from 'react';
import { ValidationService, NodeService } from '@/services';
import type { ValidationResult, ValidationError, FormState } from '../types';

interface UseNodeFormValidationOptions {
  nodeType?: string;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  formState: FormState;
  setFieldError: (field: string, error: ValidationError | null) => void;
  setErrors: (errors: Record<string, ValidationError[]>) => void;
  setValidating: (isValidating: boolean) => void;
}

/**
 * Enhanced form validation hook that integrates with ValidationService and NodeService
 * for node-specific validation using generated Zod schemas
 */
export function useNodeFormValidation({
  nodeType,
  validateOnChange = true,
  validateOnBlur = true,
  formState,
  setFieldError,
  setErrors,
  setValidating,
}: UseNodeFormValidationOptions) {
  
  // Get node specification for enhanced validation
  const nodeSpec = useMemo(() => {
    return nodeType ? NodeService.getNodeSpec(nodeType) : null;
  }, [nodeType]);

  const validateField = useCallback(async (
    field: string,
    value?: any
  ): Promise<ValidationResult> => {
    if (!nodeType) {
      return { valid: true, errors: [] };
    }

    const fieldValue = value ?? formState.data[field];
    
    try {
      setValidating(true);
      
      // Use ValidationService for field validation
      const validationMessages = ValidationService.getFieldValidationMessages(
        nodeType,
        field,
        fieldValue
      );
      
      if (validationMessages.length > 0) {
        const error: ValidationError = {
          field,
          message: validationMessages[0] || 'Validation failed', // Use first error message
        };
        setFieldError(field, error);
        
        return {
          valid: false,
          errors: [error],
        };
      } else {
        setFieldError(field, null);
        return { valid: true, errors: [] };
      }
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
  }, [nodeType, formState.data, setFieldError, setValidating]);

  const validateForm = useCallback(async (): Promise<ValidationResult> => {
    if (!nodeType) {
      return { valid: true, errors: [] };
    }

    const errors: Record<string, ValidationError[]> = {};
    const allErrors: ValidationError[] = [];
    let isValid = true;

    try {
      setValidating(true);
      
      // Validate the entire node data
      const fieldErrors = ValidationService.getFieldErrors(nodeType, formState.data);
      
      // Convert field errors to ValidationError format
      Object.entries(fieldErrors).forEach(([field, messages]) => {
        const fieldValidationErrors: ValidationError[] = (messages as string[]).map((message: string) => ({
          field,
          message,
        }));
        
        if (fieldValidationErrors.length > 0) {
          errors[field] = fieldValidationErrors;
          allErrors.push(...fieldValidationErrors);
          isValid = false;
        }
      });
      
      setErrors(errors);

      return {
        valid: isValid,
        errors: allErrors,
      };
    } finally {
      setValidating(false);
    }
  }, [nodeType, formState.data, setErrors, setValidating]);

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

  // Get field metadata for enhanced validation info
  const getFieldMetadata = useCallback((fieldName: string) => {
    if (!nodeSpec) return null;
    return nodeSpec.fields?.find((f: any) => f.name === fieldName);
  }, [nodeSpec]);

  return {
    validateField,
    validateForm,
    clearFieldError,
    clearAllErrors,
    shouldValidateOnChange,
    shouldValidateOnBlur,
    getFieldMetadata,
    nodeSpec,
  };
}