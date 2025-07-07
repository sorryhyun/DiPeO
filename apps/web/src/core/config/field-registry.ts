import type { 
  FieldType,
  FieldValidator,
  ConditionalConfig,
  OptionsConfig
} from '@/core/types/panel';
import type { NodeTypeKey } from '@/core/types/type-factories';
import {
  startFields,
  conditionFields,
  personJobFields,
  endpointFields,
  dbFields,
  jobFields,
  codeJobFields,
  apiJobFields,
  userResponseFields,
  notionFields,
  personBatchJobFields,
  hookFields,
  arrowFields,
  personFields
} from './panelConfigs';

/**
 * Unified field definition that can be used across all contexts
 */
export interface UnifiedFieldDefinition<T = any> {
  // Core properties
  name: string;
  type: FieldType;
  label: string;
  
  // Common properties
  required?: boolean;
  placeholder?: string;
  defaultValue?: unknown;
  description?: string;
  
  // UI properties
  rows?: number;
  min?: number;
  max?: number;
  disabled?: boolean | ((formData: T) => boolean);
  column?: 1 | 2;
  className?: string;
  
  // Behavior
  options?: OptionsConfig<T>;
  dependsOn?: string[];
  conditional?: ConditionalConfig<T>;
  
  // Validation
  validate?: FieldValidator<T>;
  
  // Special properties for specific field types
  labelPlaceholder?: string; // for labelPersonRow
  personPlaceholder?: string; // for labelPersonRow
  multiline?: boolean; // for textarea
  showPromptFileButton?: boolean; // for variableTextArea
  
  // Nested fields for composite types
  fields?: UnifiedFieldDefinition<T>[];
}

/**
 * Node field registry - centralized access to all node field definitions
 */
export const NODE_FIELD_REGISTRY: Record<NodeTypeKey, UnifiedFieldDefinition[]> = {
  start: startFields,
  condition: conditionFields,
  person_job: personJobFields,
  endpoint: endpointFields,
  db: dbFields,
  job: jobFields,
  code_job: codeJobFields,
  api_job: apiJobFields,
  user_response: userResponseFields,
  notion: notionFields,
  person_batch_job: personBatchJobFields,
  hook: hookFields
};

/**
 * Arrow field definitions
 */
export const ARROW_FIELD_REGISTRY = arrowFields;

/**
 * Person field definitions
 */
export const PERSON_FIELD_REGISTRY = personFields;

/**
 * Get field definitions for a specific node type
 */
export function getNodeFields(nodeType: NodeTypeKey): UnifiedFieldDefinition[] {
  return NODE_FIELD_REGISTRY[nodeType] || [];
}

/**
 * Convert unified field definition to different formats
 */
export class FieldConverter {
  /**
   * Convert to simple FieldConfig format (for nodeConfigs)
   */
  static toFieldConfig(field: UnifiedFieldDefinition): any {
    return {
      name: field.name,
      type: this.mapFieldTypeToSimple(field.type),
      label: field.label,
      required: field.required,
      placeholder: field.placeholder,
      options: Array.isArray(field.options) ? field.options : undefined,
      min: field.min,
      max: field.max,
      multiline: field.multiline,
      rows: field.rows
    };
  }
  
  /**
   * Convert to TypedPanelFieldConfig format
   */
  static toPanelFieldConfig<T>(field: UnifiedFieldDefinition<T>): any {
    return {
      type: field.type,
      name: field.name,
      label: field.label,
      placeholder: field.placeholder,
      required: field.required,
      className: field.className,
      rows: field.rows,
      min: field.min,
      max: field.max,
      labelPlaceholder: field.labelPlaceholder,
      personPlaceholder: field.personPlaceholder,
      disabled: field.disabled,
      options: field.options,
      dependsOn: field.dependsOn,
      conditional: field.conditional,
      fields: field.fields?.map(f => this.toPanelFieldConfig(f)),
      validate: field.validate,
      column: field.column
    };
  }
  
  /**
   * Map field types between different systems
   */
  private static mapFieldTypeToSimple(fieldType: FieldType): string {
    const mapping: Record<string, string> = {
      text: 'string',
      number: 'number',
      checkbox: 'boolean',
      select: 'select',
      textarea: 'textarea',
      variableTextArea: 'textarea',
      personSelect: 'person',
      labelPersonRow: 'string',
      maxIteration: 'number'
    };
    return mapping[fieldType] || 'string';
  }
}

/**
 * Validation rule registry - centralized validation logic
 */
export const VALIDATION_RULES = {
  required: (value: unknown): boolean => {
    return value !== null && value !== undefined && value !== '';
  },
  
  minLength: (value: unknown, min: number): boolean => {
    return typeof value === 'string' && value.length >= min;
  },
  
  maxLength: (value: unknown, max: number): boolean => {
    return typeof value === 'string' && value.length <= max;
  },
  
  min: (value: unknown, min: number): boolean => {
    return typeof value === 'number' && value >= min;
  },
  
  max: (value: unknown, max: number): boolean => {
    return typeof value === 'number' && value <= max;
  },
  
  pattern: (value: unknown, pattern: RegExp): boolean => {
    return typeof value === 'string' && pattern.test(value);
  },
  
  url: (value: unknown): boolean => {
    if (typeof value !== 'string') return false;
    try {
      new URL(value);
      return true;
    } catch {
      return false;
    }
  },
  
  json: (value: unknown): boolean => {
    if (typeof value !== 'string') return false;
    try {
      JSON.parse(value);
      return true;
    } catch {
      return false;
    }
  }
};

/**
 * Create a field validator from validation rules
 */
export function createFieldValidator(
  rules: Array<{ type: keyof typeof VALIDATION_RULES; params?: any[]; error: string }>
): FieldValidator {
  return (value: unknown) => {
    for (const rule of rules) {
      const validator = VALIDATION_RULES[rule.type] as any;
      const isValid = rule.params 
        ? validator(value, ...rule.params)
        : validator(value);
      
      if (!isValid) {
        return { isValid: false, error: rule.error };
      }
    }
    return { isValid: true };
  };
}