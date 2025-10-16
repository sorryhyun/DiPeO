import React, { useState, useEffect, useMemo } from 'react';
import { UnifiedFormField, UnifiedFormFieldProps } from './UnifiedFormField';
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';
import type { OptionsConfig } from '@/infrastructure/types/panel';

interface AsyncFieldWrapperProps extends Omit<UnifiedFormFieldProps, 'options'> {
  fieldDefinition: UnifiedFieldDefinition;
  formData?: Record<string, unknown>;
}

/**
 * Wrapper component that handles async options resolution for form fields
 */
export const AsyncFieldWrapper: React.FC<AsyncFieldWrapperProps> = ({
  fieldDefinition,
  formData = {},
  ...fieldProps
}) => {
  const [options, setOptions] = useState<Array<{ value: string; label: string }>>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Check if options depend on other fields
  const dependsOn = fieldDefinition.dependsOn || [];
  const dependencyValues = useMemo(() => {
    return dependsOn.map(field => formData[field]);
  }, [dependsOn, formData]);

  useEffect(() => {
    const loadOptions = async () => {
      const optionsConfig = fieldDefinition.options;

      if (!optionsConfig) {
        setOptions([]);
        return;
      }

      // If options is already an array, use it directly
      if (Array.isArray(optionsConfig)) {
        setOptions(optionsConfig);
        return;
      }

      // If options is a function, resolve it
      if (typeof optionsConfig === 'function') {
        setIsLoading(true);
        try {
          // Check if the function expects formData
          const result = await (optionsConfig as (data: Record<string, unknown>) => Promise<Array<{ value: string; label: string }>>)(formData);
          setOptions(result || []);
        } catch (error) {
          console.error(`Error loading options for field ${fieldDefinition.name}:`, error);
          setOptions([]);
        } finally {
          setIsLoading(false);
        }
      }
    };

    loadOptions();
  }, [fieldDefinition.name, fieldDefinition.options, ...dependencyValues]);

  // For select fields, pass the resolved options
  const resolvedProps: UnifiedFormFieldProps = {
    ...fieldProps,
    options,
    isLoading: isLoading || fieldProps.isLoading,
  };

  return <UnifiedFormField {...resolvedProps} />;
};

export default AsyncFieldWrapper;
