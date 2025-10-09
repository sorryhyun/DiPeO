/**
 * Validation utilities for creating consistent field specifications
 *
 * These utilities eliminate duplication between `validation` and `uiConfig`
 * by establishing a single source of truth for validation rules.
 *
 * Key principle: Define validation rules once, auto-generate UI constraints.
 */

import type { FieldSpecification, ValidationRules, UIConfiguration } from '../node-specification.js';
import type { UIInputType } from '../node-categories.js';

/**
 * Creates a validated number field with automatic UI constraint sync
 *
 * Eliminates duplication by defining min/max once and applying to both
 * validation and uiConfig automatically.
 *
 * @example
 * ```ts
 * validatedNumber Field({
 *   name: 'max_iteration',
 *   description: 'Maximum iterations',
 *   min: 1,
 *   max: 1000,
 *   defaultValue: 100,
 *   required: true
 * })
 * ```
 */
export function validatedNumberField(options: {
  name: string;
  description: string;
  min?: number;
  max?: number;
  defaultValue?: number;
  required?: boolean;
  placeholder?: string;
  column?: 1 | 2;
}): FieldSpecification {
  const {
    name,
    description,
    min,
    max,
    defaultValue,
    required = false,
    placeholder,
    column
  } = options;

  return {
    name,
    type: "number",
    required,
    ...(defaultValue !== undefined && { defaultValue }),
    description,
    ...(min !== undefined || max !== undefined ? {
      validation: {
        ...(min !== undefined && { min }),
        ...(max !== undefined && { max })
      }
    } : {}),
    uiConfig: {
      inputType: "number",
      ...(min !== undefined && { min }),
      ...(max !== undefined && { max }),
      ...(placeholder && { placeholder }),
      ...(column && { column })
    }
  };
}

/**
 * Creates a validated enum field with automatic option generation
 *
 * Single source of truth: provide enum values and labels, automatically
 * generates both validation.allowedValues and uiConfig.options.
 *
 * @example
 * ```ts
 * validatedEnumField({
 *   name: 'method',
 *   description: 'HTTP method',
 *   enumType: HttpMethod,
 *   options: [
 *     { value: HttpMethod.GET, label: 'GET' },
 *     { value: HttpMethod.POST, label: 'POST' }
 *   ],
 *   defaultValue: HttpMethod.GET,
 *   required: true
 * })
 * ```
 */
export function validatedEnumField<T extends string = string>(options: {
  name: string;
  description: string;
  options: Array<{ value: T; label: string }>;
  defaultValue?: T;
  required?: boolean;
  column?: 1 | 2;
  conditional?: FieldSpecification['conditional'];
}): FieldSpecification {
  const {
    name,
    description,
    options: selectOptions,
    defaultValue,
    required = true,
    column,
    conditional
  } = options;

  // Extract allowed values from options - single source of truth
  const allowedValues = selectOptions.map(opt => opt.value);

  return {
    name,
    type: "enum",
    required,
    ...(defaultValue !== undefined && { defaultValue }),
    description,
    validation: {
      allowedValues
    },
    uiConfig: {
      inputType: "select",
      options: selectOptions,
      ...(column && { column })
    },
    ...(conditional && { conditional })
  };
}

/**
 * Creates a validated text field with pattern validation
 *
 * @example
 * ```ts
 * validatedTextField({
 *   name: 'webhook_url',
 *   description: 'Webhook URL',
 *   pattern: '^https?://.+',
 *   placeholder: 'https://example.com/webhook'
 * })
 * ```
 */
export function validatedTextField(options: {
  name: string;
  description: string;
  pattern?: string;
  minLength?: number;
  maxLength?: number;
  placeholder?: string;
  required?: boolean;
  defaultValue?: string;
  column?: 1 | 2;
}): FieldSpecification {
  const {
    name,
    description,
    pattern,
    minLength,
    maxLength,
    placeholder,
    required = false,
    defaultValue,
    column
  } = options;

  const hasValidation = pattern || minLength !== undefined || maxLength !== undefined;

  return {
    name,
    type: "string",
    required,
    ...(defaultValue !== undefined && { defaultValue }),
    description,
    ...(hasValidation ? {
      validation: {
        ...(pattern && { pattern }),
        ...(minLength !== undefined && { minLength }),
        ...(maxLength !== undefined && { maxLength })
      }
    } : {}),
    uiConfig: {
      inputType: "text",
      ...(placeholder && { placeholder }),
      ...(column && { column })
    }
  };
}

/**
 * Creates a validated array field with item type validation
 *
 * @example
 * ```ts
 * validatedArrayField({
 *   name: 'node_indices',
 *   description: 'Node indices to monitor',
 *   itemType: 'string',
 *   inputType: 'nodeSelect'
 * })
 * ```
 */
export function validatedArrayField(options: {
  name: string;
  description: string;
  itemType: 'string' | 'number' | 'boolean' | 'enum';
  inputType?: UIInputType;
  placeholder?: string;
  required?: boolean;
  conditional?: FieldSpecification['conditional'];
}): FieldSpecification {
  const {
    name,
    description,
    itemType,
    inputType = 'text',
    placeholder,
    required = false,
    conditional
  } = options;

  return {
    name,
    type: "array",
    required,
    description,
    validation: {
      itemType
    },
    uiConfig: {
      inputType,
      ...(placeholder && { placeholder })
    },
    ...(conditional && { conditional })
  };
}

/**
 * Merge validation rules into a field specification
 *
 * Utility for applying validation rules to an existing field while
 * keeping uiConfig in sync.
 */
export function withValidation(
  field: FieldSpecification,
  validation: ValidationRules
): FieldSpecification {
  const updatedUiConfig = { ...field.uiConfig };

  // Sync numeric constraints to UI
  if (validation.min !== undefined) {
    updatedUiConfig.min = validation.min;
  }
  if (validation.max !== undefined) {
    updatedUiConfig.max = validation.max;
  }

  return {
    ...field,
    validation: {
      ...field.validation,
      ...validation
    },
    uiConfig: updatedUiConfig
  };
}

/**
 * Helper: Create enum options from an object enum
 *
 * Converts TypeScript enum object to options array for validatedEnumField.
 *
 * @example
 * ```ts
 * const HttpMethod = {
 *   GET: 'GET',
 *   POST: 'POST'
 * } as const;
 *
 * validatedEnumField({
 *   name: 'method',
 *   description: 'HTTP method',
 *   options: enumToOptions(HttpMethod)
 * })
 * ```
 */
export function enumToOptions<T extends Record<string, string>>(
  enumObj: T,
  customLabels?: Partial<Record<keyof T, string>>
): Array<{ value: T[keyof T]; label: string }> {
  return Object.entries(enumObj).map(([key, value]) => ({
    value: value as T[keyof T],
    label: customLabels?.[key as keyof T] || key.split('_').map(
      word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ')
  }));
}

/**
 * Helper: Infer UI config from validation rules
 *
 * Automatically generates appropriate uiConfig based on validation rules.
 * Useful for programmatic field generation.
 */
export function inferUIConfig(
  inputType: UIInputType,
  validation?: ValidationRules,
  baseConfig?: Partial<UIConfiguration>
): UIConfiguration {
  const uiConfig: UIConfiguration = {
    inputType,
    ...baseConfig
  };

  // Apply numeric constraints
  if (validation?.min !== undefined) {
    uiConfig.min = validation.min;
  }
  if (validation?.max !== undefined) {
    uiConfig.max = validation.max;
  }

  return uiConfig;
}

/**
 * Validation preset builder
 *
 * Provides common validation rule sets for typical use cases.
 */
export const ValidationPresets = {
  /**
   * Timeout validation (1-3600 seconds)
   */
  timeout: (min = 0, max = 3600): ValidationRules => ({
    min,
    max
  }),

  /**
   * Retry count validation (0-10)
   */
  retryCount: (min = 0, max = 10): ValidationRules => ({
    min,
    max
  }),

  /**
   * Port number validation (1-65535)
   */
  port: (): ValidationRules => ({
    min: 1,
    max: 65535
  }),

  /**
   * Percentage validation (0-100)
   */
  percentage: (): ValidationRules => ({
    min: 0,
    max: 100
  }),

  /**
   * Positive integer validation (min 1)
   */
  positiveInteger: (max?: number): ValidationRules => ({
    min: 1,
    ...(max !== undefined && { max })
  }),

  /**
   * URL pattern validation
   */
  url: (): ValidationRules => ({
    pattern: '^https?://.+'
  }),

  /**
   * Email pattern validation
   */
  email: (): ValidationRules => ({
    pattern: '^[^@]+@[^@]+\\.[^@]+$'
  }),

  /**
   * File path validation
   */
  filePath: (): ValidationRules => ({
    pattern: '^[^\\0]+$' // No null bytes
  })
};
