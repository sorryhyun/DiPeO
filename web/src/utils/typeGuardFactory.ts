/**
 * Type Guard Factory
 * 
 * Reduces duplication in type guard creation and provides
 * consistent patterns for runtime type checking.
 */

// Type for property check configuration
interface PropertyCheck {
  key: string;
  type?: 'string' | 'number' | 'boolean' | 'object' | 'function';
  validator?: (value: unknown) => boolean;
  enum?: readonly unknown[];
}

// Type for the type guard function
type TypeGuard<T> = (obj: unknown) => obj is T;

// Configuration for creating type guards
interface TypeGuardConfig {
  properties: PropertyCheck[];
  additionalChecks?: (obj: any) => boolean;
}

/**
 * Creates a type guard function from configuration
 */
export function createTypeGuard<T>(config: TypeGuardConfig): TypeGuard<T> {
  return (obj: unknown): obj is T => {
    // Basic object check
    if (!obj || typeof obj !== 'object') return false;
    
    const record = obj as Record<string, unknown>;
    
    // Check all required properties
    for (const check of config.properties) {
      // Check if property exists
      if (!(check.key in record)) return false;
      
      const value = record[check.key];
      
      // Type check
      if (check.type && typeof value !== check.type) return false;
      
      // Enum check
      if (check.enum && !check.enum.includes(value)) return false;
      
      // Custom validator
      if (check.validator && !check.validator(value)) return false;
    }
    
    // Additional checks
    if (config.additionalChecks && !config.additionalChecks(record)) {
      return false;
    }
    
    return true;
  };
}

/**
 * Creates a type guard for enum values
 */
export function createEnumGuard<T extends string>(
  validValues: readonly T[]
): TypeGuard<T> {
  return (value: unknown): value is T => {
    return typeof value === 'string' && validValues.includes(value as T);
  };
}

/**
 * Creates a type guard for branded types
 */
export function createBrandedTypeGuard<T extends { __brand: string }>(
  validator: (value: string) => boolean
): TypeGuard<T> {
  return (value: unknown): value is T => {
    return typeof value === 'string' && validator(value);
  };
}

/**
 * Creates a type guard for collections
 */
export function createCollectionGuard<T>(
  itemGuard: TypeGuard<T>
): TypeGuard<T[]> {
  return (value: unknown): value is T[] => {
    return Array.isArray(value) && value.every(itemGuard);
  };
}

/**
 * Creates a type guard for Map values
 */
export function createMapGuard<K, V>(
  keyGuard: TypeGuard<K>,
  valueGuard: TypeGuard<V>
): TypeGuard<Map<K, V>> {
  return (value: unknown): value is Map<K, V> => {
    if (!(value instanceof Map)) return false;
    
    for (const [k, v] of value) {
      if (!keyGuard(k) || !valueGuard(v)) return false;
    }
    
    return true;
  };
}

/**
 * Creates a type guard for nullable types
 */
export function createNullableGuard<T>(
  guard: TypeGuard<T>
): TypeGuard<T | null | undefined> {
  return (value: unknown): value is T | null | undefined => {
    return value === null || value === undefined || guard(value);
  };
}

/**
 * Combines multiple type guards with OR logic
 */
export function createUnionGuard<T extends readonly unknown[]>(
  ...guards: { [K in keyof T]: TypeGuard<T[K]> }
): TypeGuard<T[number]> {
  return (value: unknown): value is T[number] => {
    return guards.some(guard => guard(value));
  };
}

/**
 * Creates a type guard for objects with specific shape
 */
export function createShapeGuard<T extends Record<string, unknown>>(
  shape: { [K in keyof T]: TypeGuard<T[K]> }
): TypeGuard<T> {
  return (obj: unknown): obj is T => {
    if (!obj || typeof obj !== 'object') return false;
    
    const record = obj as Record<string, unknown>;
    
    for (const [key, guard] of Object.entries(shape)) {
      if (!guard(record[key])) return false;
    }
    
    return true;
  };
}

/**
 * Creates a partial type guard (all properties optional)
 */
export function createPartialGuard<T>(
  fullGuard: TypeGuard<T>,
  requiredKeys: (keyof T)[] = []
): TypeGuard<Partial<T>> {
  return (obj: unknown): obj is Partial<T> => {
    if (!obj || typeof obj !== 'object') return false;
    
    const record = obj as Record<string, unknown>;
    
    // Check required keys exist
    for (const key of requiredKeys) {
      if (!(key as string in record)) return false;
    }
    
    // Create a temporary object with only defined properties
    const definedProps = Object.entries(record).reduce((acc, [key, value]) => {
      if (value !== undefined) {
        acc[key] = value;
      }
      return acc;
    }, {} as Record<string, unknown>);
    
    // Check if defined properties would pass the full guard
    return Object.keys(definedProps).length === 0 || fullGuard(definedProps);
  };
}

// Utility type guard creators for common patterns

/**
 * Creates a string type guard with optional pattern
 */
export const isString = (pattern?: RegExp): TypeGuard<string> => 
  (value: unknown): value is string => {
    return typeof value === 'string' && (!pattern || pattern.test(value));
  };

/**
 * Creates a number type guard with optional range
 */
export const isNumber = (min?: number, max?: number): TypeGuard<number> =>
  (value: unknown): value is number => {
    return typeof value === 'number' && 
           !isNaN(value) &&
           (min === undefined || value >= min) &&
           (max === undefined || value <= max);
  };

/**
 * Creates a literal type guard
 */
export const isLiteral = <T extends string | number | boolean>(
  literal: T
): TypeGuard<T> =>
  (value: unknown): value is T => value === literal;

// Re-export for convenience
export type { TypeGuard, TypeGuardConfig, PropertyCheck };