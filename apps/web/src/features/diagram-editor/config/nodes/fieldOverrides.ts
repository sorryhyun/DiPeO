import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';
import { getGeneratedFields } from './generated-fields';
import { createZodFieldValidator } from './generated-schemas';

/**
 * Field override configuration for specific node types
 * These overrides are applied on top of the generated field configs
 */
export interface FieldOverrides {
  [nodeType: string]: {
    // Fields to completely remove from the generated config
    excludeFields?: string[];
    
    // Field-specific overrides (partial updates)
    fieldOverrides?: {
      [fieldName: string]: Partial<UnifiedFieldDefinition>;
    };
    
    // Additional custom fields not in the domain model
    additionalFields?: UnifiedFieldDefinition[];
    
    // Custom field order (if not specified, uses generated order)
    fieldOrder?: string[];
  };
}

/**
 * UI-specific field overrides for each node type
 */
export const NODE_FIELD_OVERRIDES: FieldOverrides = {
  start: {
    fieldOverrides: {
      custom_data: {
        placeholder: 'Enter custom data as JSON',
        description: 'Custom data that will be passed to the first node'
      },
      output_data_structure: {
        placeholder: 'Define the expected output structure as JSON',
        description: 'The structure that the endpoint will return'
      },
      trigger_mode: {
        type: 'select',
        options: [
          { value: 'manual', label: 'Manual' },
          { value: 'hook', label: 'Hook' }
        ]
      }
    }
  },
  
  person_job: {
    excludeFields: ['person', 'memory_config', 'memory_settings'], // person handled by labelPersonRow, memory fields excluded
    fieldOverrides: {
      tools: {
        placeholder: 'Optional tools configuration',
        rows: 2
      },
      first_only_prompt: {
        required: true,
        placeholder: 'Prompt to use only on first execution.',
        rows: 4,
        column: 2,
        showPromptFileButton: true,
        validate: (value: unknown) => {
          if (!value || typeof value !== 'string' || value.trim().length === 0) {
            return { isValid: false, error: 'First-only prompt is required' };
          }
          return { isValid: true };
        }
      },
      default_prompt: {
        column: 2,
        showPromptFileButton: true,
        validate: (value: unknown) => {
          if (!value && typeof value !== 'string') {
            return { isValid: false, error: 'Default prompt is recommended' };
          }
          return { isValid: true };
        }
      }
    },
    additionalFields: [
      {
        name: 'labelPersonRow',
        type: 'labelPersonRow',
        label: '',
        required: true,
        labelPlaceholder: 'Enter block label',
        personPlaceholder: 'Select a person'
      },
      {
        name: 'memory_profile',
        type: 'select',
        label: 'Memory Profile',
        options: [
          { value: 'FULL', label: 'Full (No limits, see everything)' },
          { value: 'FOCUSED', label: 'Focused (Last 20 messages, conversation pairs)' },
          { value: 'MINIMAL', label: 'Minimal (Last 5 messages, system + direct)' },
          { value: 'GOLDFISH', label: 'Goldfish (Last 2 exchanges only)' },
          { value: 'CUSTOM', label: 'Custom (Configure manually)' }
        ],
        defaultValue: 'FULL',
        description: 'Predefined memory configurations for different use cases'
      }
    ],
    fieldOrder: ['labelPersonRow', 'max_iteration', 'tools', 'memory_profile', 'default_prompt', 'first_only_prompt']
  },
  
  condition: {
    fieldOverrides: {
      condition_type: {
        type: 'select',
        options: [
          { value: 'detect_max_iterations', label: 'Detect Max Iterations' },
          { value: 'check_nodes_executed', label: 'Check Nodes Executed' },
          { value: 'custom', label: 'Custom Expression' }
        ]
      },
      expression: {
        placeholder: 'Enter condition expression (e.g., {{value}} > 10)'
      }
    }
  },
  
  api_job: {
    fieldOverrides: {
      method: {
        defaultValue: 'GET'
      },
      headers: {
        placeholder: 'Headers as JSON (e.g., {"Authorization": "Bearer {{token}}"})'
      },
      timeout: {
        defaultValue: 30
      }
    }
  },
  
  code_job: {
    fieldOverrides: {
      language: {
        defaultValue: 'python'
      },
      code: {
        placeholder: 'Enter your code here. Use {{variable}} for input variables.'
      }
    }
  },
  
  db: {
    fieldOverrides: {
      sub_type: {
        defaultValue: 'fixed_prompt'
      },
      operation: {
        type: 'select',
        options: [
          { value: 'create', label: 'Create' },
          { value: 'read', label: 'Read' },
          { value: 'update', label: 'Update' },
          { value: 'delete', label: 'Delete' }
        ]
      }
    }
  },
  
  hook: {
    fieldOverrides: {
      timeout: {
        defaultValue: 60
      },
      retry_count: {
        defaultValue: 3
      },
      retry_delay: {
        defaultValue: 5
      }
    }
  }
};

/**
 * Merge generated fields with UI-specific overrides
 */
export function mergeFieldConfigs(nodeType: string, options?: { 
  useZodValidation?: boolean 
}): UnifiedFieldDefinition[] {
  const { useZodValidation = true } = options || {};
  
  // Get base generated fields
  const generatedFields = getGeneratedFields(nodeType);
  const overrides = NODE_FIELD_OVERRIDES[nodeType];
  
  // Add Zod validation to generated fields if enabled
  let fields = generatedFields.map(field => {
    if (useZodValidation && !field.validate) {
      return {
        ...field,
        validate: createZodFieldValidator(nodeType, field.name)
      };
    }
    return field;
  });
  
  if (!overrides) {
    return fields;
  }
  
  // Remove excluded fields
  if (overrides.excludeFields) {
    fields = fields.filter(field => !overrides.excludeFields!.includes(field.name));
  }
  
  // Apply field overrides
  if (overrides.fieldOverrides) {
    fields = fields.map(field => {
      const fieldOverride = overrides.fieldOverrides![field.name];
      if (fieldOverride) {
        // Preserve Zod validation unless explicitly overridden
        const mergedField = { ...field, ...fieldOverride };
        if (!fieldOverride.validate && field.validate && useZodValidation) {
          mergedField.validate = field.validate;
        }
        return mergedField;
      }
      return field;
    });
  }
  
  // Add additional fields
  if (overrides.additionalFields) {
    fields = [...fields, ...overrides.additionalFields];
  }
  
  // Apply custom field order if specified
  if (overrides.fieldOrder) {
    const orderedFields: UnifiedFieldDefinition[] = [];
    const fieldMap = new Map(fields.map(f => [f.name, f]));
    
    // Add fields in specified order
    for (const fieldName of overrides.fieldOrder) {
      const field = fieldMap.get(fieldName);
      if (field) {
        orderedFields.push(field);
        fieldMap.delete(fieldName);
      }
    }
    
    // Add any remaining fields not in the order
    orderedFields.push(...fieldMap.values());
    
    return orderedFields;
  }
  
  return fields;
}

/**
 * Check if a node type has overrides
 */
export function hasFieldOverrides(nodeType: string): boolean {
  return nodeType in NODE_FIELD_OVERRIDES;
}