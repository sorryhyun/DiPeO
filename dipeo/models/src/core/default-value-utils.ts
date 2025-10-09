/**
 * Default value utilities for node specifications
 *
 * These utilities standardize how default values are specified across:
 * 1. TypeScript field specifications
 * 2. Python code generation
 * 3. GraphQL schemas
 *
 * Key principle: TypeScript specs are the single source of truth for defaults.
 */

/**
 * Default value types supported across the system
 */
export type DefaultValue =
  | string
  | number
  | boolean
  | null
  | undefined
  | Record<string, any>
  | any[];

/**
 * Default value configuration for different contexts
 */
export interface DefaultValueConfig {
  /**
   * TypeScript/JavaScript default value
   * Used in node specifications and frontend
   */
  tsValue: DefaultValue;

  /**
   * Python default value syntax
   * Used in code generation for Python dataclasses
   */
  pyValue?: string;

  /**
   * GraphQL default value
   * Used in schema generation
   */
  gqlValue?: any;

  /**
   * Description of the default value
   */
  description?: string;
}

/**
 * Common default value presets for typical use cases
 */
export const DefaultValuePresets = {
  /**
   * Empty string default
   */
  emptyString: (): DefaultValueConfig => ({
    tsValue: '',
    pyValue: '""',
    gqlValue: '',
    description: 'Empty string'
  }),

  /**
   * Empty object default
   */
  emptyObject: (): DefaultValueConfig => ({
    tsValue: {},
    pyValue: 'field(default_factory=dict)',
    gqlValue: null,
    description: 'Empty object'
  }),

  /**
   * Empty array default
   */
  emptyArray: <T = any>(): DefaultValueConfig => ({
    tsValue: [],
    pyValue: 'field(default_factory=list)',
    gqlValue: null,
    description: 'Empty array'
  }),

  /**
   * Boolean false default
   */
  false: (): DefaultValueConfig => ({
    tsValue: false,
    pyValue: 'False',
    gqlValue: false,
    description: 'Boolean false'
  }),

  /**
   * Boolean true default
   */
  true: (): DefaultValueConfig => ({
    tsValue: true,
    pyValue: 'True',
    gqlValue: true,
    description: 'Boolean true'
  }),

  /**
   * Numeric default
   */
  number: (value: number): DefaultValueConfig => ({
    tsValue: value,
    pyValue: String(value),
    gqlValue: value,
    description: `Number: ${value}`
  }),

  /**
   * String default
   */
  string: (value: string): DefaultValueConfig => ({
    tsValue: value,
    pyValue: `"${value}"`,
    gqlValue: value,
    description: `String: "${value}"`
  }),

  /**
   * Enum default
   */
  enum: <T extends string>(
    enumType: string,
    value: T
  ): DefaultValueConfig => ({
    tsValue: value,
    pyValue: `field(default=${enumType}.${value})`,
    gqlValue: value,
    description: `Enum: ${enumType}.${value}`
  }),

  /**
   * Array of specific values
   */
  arrayOfValues: <T = any>(values: T[]): DefaultValueConfig => ({
    tsValue: values,
    pyValue: `field(default_factory=lambda: ${JSON.stringify(values)})`,
    gqlValue: null,
    description: `Array: ${JSON.stringify(values)}`
  })
};

/**
 * Infers Python default value syntax from TypeScript default value
 *
 * @param tsValue - TypeScript default value
 * @param fieldType - Field type (for context)
 * @param enumType - Enum type name (if field is enum)
 * @returns Python default value syntax
 */
export function inferPythonDefault(
  tsValue: DefaultValue,
  fieldType?: string,
  enumType?: string
): string {
  // Handle undefined/null
  if (tsValue === undefined || tsValue === null) {
    return 'None';
  }

  // Handle strings
  if (typeof tsValue === 'string') {
    // Empty string
    if (tsValue === '') {
      return '""';
    }
    // Enum value (if enumType is provided)
    if (enumType) {
      return `field(default=${enumType}.${tsValue.toUpperCase().replace(/-/g, '_')})`;
    }
    // Regular string
    return `"${tsValue}"`;
  }

  // Handle numbers
  if (typeof tsValue === 'number') {
    return String(tsValue);
  }

  // Handle booleans
  if (typeof tsValue === 'boolean') {
    return tsValue ? 'True' : 'False';
  }

  // Handle arrays
  if (Array.isArray(tsValue)) {
    if (tsValue.length === 0) {
      return 'field(default_factory=list)';
    }
    // Array with specific default values
    return `field(default_factory=lambda: ${JSON.stringify(tsValue)})`;
  }

  // Handle objects
  if (typeof tsValue === 'object') {
    if (Object.keys(tsValue).length === 0) {
      return 'field(default_factory=dict)';
    }
    // Object with specific default values
    return `field(default_factory=lambda: ${JSON.stringify(tsValue)})`;
  }

  // Fallback
  return 'None';
}

/**
 * Creates a consistent default value configuration
 *
 * This is the recommended way to specify defaults in field specifications.
 *
 * @example
 * ```ts
 * // Simple defaults
 * createDefaultValue(false)  // Boolean
 * createDefaultValue("")     // Empty string
 * createDefaultValue(100)    // Number
 *
 * // Enum defaults
 * createDefaultValue(HttpMethod.GET, {
 *   enumType: 'HttpMethod'
 * })
 *
 * // Complex defaults
 * createDefaultValue([], {
 *   description: 'Empty array of items'
 * })
 * ```
 */
export function createDefaultValue(
  tsValue: DefaultValue,
  options?: {
    enumType?: string;
    fieldType?: string;
    pyValue?: string;  // Override auto-inferred Python value
    description?: string;
  }
): DefaultValueConfig {
  const {
    enumType,
    fieldType,
    pyValue,
    description
  } = options || {};

  return {
    tsValue,
    pyValue: pyValue || inferPythonDefault(tsValue, fieldType, enumType),
    gqlValue: tsValue,
    description
  };
}

/**
 * Validates that a default value is appropriate for the field type
 *
 * @param defaultValue - Default value to validate
 * @param fieldType - Expected field type
 * @returns Validation result with error message if invalid
 */
export function validateDefaultValue(
  defaultValue: DefaultValue,
  fieldType: string
): { valid: boolean; error?: string } {
  // Undefined/null is always valid (no default)
  if (defaultValue === undefined || defaultValue === null) {
    return { valid: true };
  }

  // Type-specific validation
  switch (fieldType) {
    case 'string':
      if (typeof defaultValue !== 'string') {
        return {
          valid: false,
          error: `Default value must be string, got ${typeof defaultValue}`
        };
      }
      break;

    case 'number':
      if (typeof defaultValue !== 'number') {
        return {
          valid: false,
          error: `Default value must be number, got ${typeof defaultValue}`
        };
      }
      break;

    case 'boolean':
      if (typeof defaultValue !== 'boolean') {
        return {
          valid: false,
          error: `Default value must be boolean, got ${typeof defaultValue}`
        };
      }
      break;

    case 'array':
      if (!Array.isArray(defaultValue)) {
        return {
          valid: false,
          error: `Default value must be array, got ${typeof defaultValue}`
        };
      }
      break;

    case 'object':
      if (typeof defaultValue !== 'object' || Array.isArray(defaultValue)) {
        return {
          valid: false,
          error: `Default value must be object, got ${typeof defaultValue}`
        };
      }
      break;
  }

  return { valid: true };
}

/**
 * Helper: Extract default value from field specification
 */
export function getDefaultValue(field: any): DefaultValue {
  return field.defaultValue;
}

/**
 * Helper: Check if field has a default value
 */
export function hasDefaultValue(field: any): boolean {
  return field.defaultValue !== undefined;
}
