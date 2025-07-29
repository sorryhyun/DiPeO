/**
 * GraphQL utility functions
 */

// Known enum fields that need case conversion
const ENUM_FIELDS = new Set([
  'label',
  'direction', 
  'data_type',
  'type',
  'status',
  'operation',
  'content_type',
  'sub_type',
  'condition_type',
  'service',
  'method',
  'hook_type',
  'trigger_mode'
]);

// Special enum value mappings (for cases where the enum value doesn't match the key)
const ENUM_VALUE_MAPPINGS: Record<string, string> = {
  // HandleLabel mappings
  'condition_true': 'condtrue',
  'condition_false': 'condfalse',
  'CONDITION_TRUE': 'condtrue',
  'CONDITION_FALSE': 'condfalse',
  'CONDTRUE': 'condtrue',
  'CONDFALSE': 'condfalse',
  // Add other special cases as needed
};

/**
 * Recursively removes all __typename fields from an object and converts enum values to lowercase
 * This is needed because:
 * 1. Apollo Client adds __typename fields for caching, but the backend Pydantic models don't expect these fields
 * 2. GraphQL enums are uppercase but backend expects lowercase
 */
export function stripTypenames<T>(obj: T): T {
  if (obj === null || obj === undefined) {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(item => stripTypenames(item)) as unknown as T;
  }

  if (typeof obj === 'object') {
    const result: any = {};
    for (const key in obj) {
      if (key !== '__typename' && obj.hasOwnProperty(key)) {
        let value = (obj as any)[key];
        
        // Convert enum values
        if (ENUM_FIELDS.has(key) && typeof value === 'string') {
          // First check if there's a special mapping
          if (ENUM_VALUE_MAPPINGS[value]) {
            value = ENUM_VALUE_MAPPINGS[value];
          } else {
            // Otherwise just convert to lowercase
            value = value.toLowerCase();
          }
        }
        
        result[key] = stripTypenames(value);
      }
    }
    return result as T;
  }

  return obj;
}

/**
 * Strips __typename fields from a diagram object specifically
 * This is a convenience function for the common use case
 */
export function stripDiagramTypenames(diagram: any): any {
  return stripTypenames(diagram);
}