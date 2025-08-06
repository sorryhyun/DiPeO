import { useCallback, useMemo } from 'react';
import { useFormState } from './useFormState';
import { useFormValidation } from './useFormValidation';
import { useFormAutoSave } from './useFormAutoSave';
import { useMultipleAsyncFieldOptions } from './useAsyncFieldOptions';
import type {
  FormConfig,
  FormOperations,
  FormAutoSaveConfig,
  AsyncFieldOptions,
  FormFieldUpdate,
} from '../types';

export interface UseFormManagerOptions<T extends Record<string, any>> {
  config: FormConfig<T>;
  autoSave?: FormAutoSaveConfig;
  asyncFields?: Record<string, AsyncFieldOptions>;
  onSubmit?: (values: T) => Promise<void> | void;
}

export function useFormManager<T extends Record<string, any>>({
  config,
  autoSave,
  asyncFields = {},
  onSubmit,
}: UseFormManagerOptions<T>) {
  const {
    formState,
    operations: stateOperations,
    computed,
  } = useFormState(config);

  const validation = useFormValidation({
    validators: config.validators,
    validateOnChange: config.validateOnChange,
    validateOnBlur: config.validateOnBlur,
    formState,
    setFieldError: stateOperations.setFieldError,
    setErrors: stateOperations.setErrors,
    setValidating: stateOperations.setValidating,
  });

  const autoSaveState = autoSave
    ? useFormAutoSave({
        config: autoSave,
        formState,
        hasErrors: computed.hasErrors,
      })
    : null;

  const asyncFieldQueries = useMultipleAsyncFieldOptions(asyncFields, formState);

  const updateField = useCallback(async (update: FormFieldUpdate) => {
    stateOperations.updateField(update);

    if (update.validate !== false && validation.shouldValidateOnChange(update.field)) {
      await validation.validateField(update.field, update.value);
    }
  }, [stateOperations, validation]);

  const updateFields = useCallback(async (updates: Partial<T>) => {
    stateOperations.updateFields(updates);

    if (config.validateOnChange) {
      const fieldsToValidate = Object.keys(updates).filter(field => 
        formState.touched[field]
      );
      
      await Promise.all(
        fieldsToValidate.map(field => validation.validateField(field))
      );
    }
  }, [stateOperations, config.validateOnChange, formState.touched, validation]);

  const handleBlur = useCallback(async (field: string) => {
    stateOperations.setFieldTouched(field);

    if (validation.shouldValidateOnBlur()) {
      await validation.validateField(field);
    }
  }, [stateOperations, validation]);

  const submit = useCallback(async () => {
    if (formState.isSubmitting) return;

    try {
      stateOperations.setSubmitting(true);
      
      Object.keys(formState.data).forEach(field => {
        stateOperations.setFieldTouched(field);
      });

      const validationResult = await validation.validateForm();
      
      if (!validationResult.valid) {
        return;
      }

      if (onSubmit) {
        await onSubmit(formState.data);
      }

      if (autoSaveState) {
        autoSaveState.resetAutoSave();
      }
    } finally {
      stateOperations.setSubmitting(false);
    }
  }, [
    formState.isSubmitting,
    formState.data,
    stateOperations,
    validation,
    onSubmit,
    autoSaveState,
  ]);

  const reset = useCallback((values?: Partial<T>) => {
    stateOperations.reset(values);
    validation.clearAllErrors();
    
    if (autoSaveState) {
      autoSaveState.resetAutoSave();
    }
  }, [stateOperations, validation, autoSaveState]);

  const operations: FormOperations<T> = useMemo(() => ({
    updateField,
    updateFields,
    setFieldError: stateOperations.setFieldError,
    setFieldTouched: stateOperations.setFieldTouched,
    validateField: validation.validateField,
    validateForm: validation.validateForm,
    reset,
    submit,
  }), [
    updateField,
    updateFields,
    stateOperations,
    validation,
    reset,
    submit,
  ]);

  return {
    formState,
    operations,
    validation: {
      validateField: validation.validateField,
      validateForm: validation.validateForm,
      clearFieldError: validation.clearFieldError,
      clearAllErrors: validation.clearAllErrors,
    },
    computed: {
      ...computed,
      isValid: !computed.hasErrors && computed.isTouched,
      canSubmit: !computed.hasErrors && !formState.isSubmitting,
    },
    autoSave: autoSaveState,
    asyncFields: asyncFieldQueries,
    handlers: {
      handleBlur,
      handleSubmit: submit,
    },
  };
}