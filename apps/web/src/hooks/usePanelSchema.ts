import { useMemo } from 'react';
import { useQueries } from '@tanstack/react-query';
import { UseFormReturn } from 'react-hook-form';
import { PanelConfig, PanelFieldConfig, SelectFieldConfig } from '@/types';

interface ProcessedField {
  field: PanelFieldConfig;
  options?: Array<{ value: string; label: string }>;
  isLoading?: boolean;
  error?: Error | null;
}

export function usePanelSchema<T extends Record<string, unknown>>(
  config: PanelConfig<T>,
  form: UseFormReturn<T, any>
) {
  // Flatten all fields from different layout sections
  const fields = useMemo(() => {
    const flattenFields = (fields: PanelFieldConfig[]): PanelFieldConfig[] => {
      const result: PanelFieldConfig[] = [];
      
      fields.forEach(field => {
        if (field.type === 'row' && field.fields) {
          result.push(...flattenFields(field.fields));
        } else {
          result.push(field);
        }
      });
      
      return result;
    };
    
    let allFields: PanelFieldConfig[] = [];
    
    if (config.fields) {
      allFields = allFields.concat(flattenFields(config.fields));
    }
    if (config.leftColumn) {
      allFields = allFields.concat(flattenFields(config.leftColumn));
    }
    if (config.rightColumn) {
      allFields = allFields.concat(flattenFields(config.rightColumn));
    }
    
    return allFields;
  }, [config]);

  // Filter fields that need async options
  const asyncFields = useMemo(() => {
    return fields.filter(
      field => field.type === 'select' && typeof field.options === 'function'
    ) as SelectFieldConfig[];
  }, [fields]);

  // Create queries for async fields
  const queries = useQueries({
    queries: asyncFields.map(field => {
      const getDependencyValues = () => {
        if (!field.dependsOn) return [];
        
        // Watch specific fields if dependsOn is specified
        const dependencies = Array.isArray(field.dependsOn) ? field.dependsOn : [field.dependsOn];
        return dependencies.map(dep => form.watch(dep as any));
      };

      const checkDependencies = () => {
        if (!field.dependsOn) return true;
        
        // Check if all dependencies have values
        const dependencies = Array.isArray(field.dependsOn) ? field.dependsOn : [field.dependsOn];
        return dependencies.every(dep => {
          const value = form.watch(dep as any);
          return value !== undefined && value !== null && value !== '';
        });
      };

      return {
        queryKey: ['field-options', field.name, ...getDependencyValues()],
        queryFn: async () => {
          const optionsFn = field.options as (formData?: T) => Promise<Array<{ value: string; label: string }>>;
          
          // If field has dependencies, pass formData
          if (field.dependsOn) {
            const formData = form.getValues();
            return await optionsFn(formData);
          }
          
          // Otherwise, call without formData
          return await optionsFn();
        },
        enabled: checkDependencies(),
        staleTime: 5 * 60 * 1000, // Cache for 5 minutes
        cacheTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
      };
    })
  });

  // Create a map of field names to their query results
  const optionsMap = useMemo(() => {
    const map = new Map<string, ProcessedField['options']>();
    const loadingMap = new Map<string, boolean>();
    const errorMap = new Map<string, Error | null>();
    
    asyncFields.forEach((field, index) => {
      const query = queries[index];
      if (field.name && query) {
        map.set(field.name, query.data || []);
        loadingMap.set(field.name, query.isLoading);
        errorMap.set(field.name, query.error);
      }
    });
    
    return { options: map, loading: loadingMap, errors: errorMap };
  }, [asyncFields, queries]);

  // Process all fields with their options
  const processedFields = useMemo(() => {
    return fields.map(field => {
      const processed: ProcessedField = { field };
      
      if (field.type === 'select' && field.name) {
        if (typeof field.options === 'function') {
          processed.options = optionsMap.options.get(field.name) || [];
          processed.isLoading = optionsMap.loading.get(field.name) || false;
          processed.error = optionsMap.errors.get(field.name) || null;
        } else if (Array.isArray(field.options)) {
          processed.options = field.options;
        }
      }
      
      return processed;
    });
  }, [fields, optionsMap]);

  return processedFields;
}