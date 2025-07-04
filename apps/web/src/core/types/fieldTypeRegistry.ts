import { FIELD_TYPES, FieldType } from './panel'

// Domain field types as used in TypeScript models
export type DomainFieldType = 
  | 'string' 
  | 'number' 
  | 'boolean' 
  | 'select' 
  | 'textarea' 
  | 'person';

// Extended field types for properties editor
export type ExtendedFieldType = 
  | DomainFieldType 
  | 'json' 
  | 'array' 
  | 'object' 
  | 'email' 
  | 'url';

// Legacy field type names that need to be maintained for backward compatibility
export type LegacyFieldType = 
  | 'checkbox' 
  | 'iteration-count' 
  | 'person-select' 
  | 'variable-textarea';

// All possible field type inputs
export type AnyFieldType = DomainFieldType | ExtendedFieldType | LegacyFieldType | FieldType;

/**
 * Central registry for all field type mappings
 */
export const FIELD_TYPE_REGISTRY = {
  // Domain to UI field type mappings
  domain: {
    'string': FIELD_TYPES.TEXT,
    'number': FIELD_TYPES.NUMBER,
    'boolean': FIELD_TYPES.BOOLEAN,
    'select': FIELD_TYPES.SELECT,
    'textarea': FIELD_TYPES.VARIABLE_TEXTAREA,
    'person': FIELD_TYPES.PERSON_SELECT,
  } as const satisfies Record<DomainFieldType, FieldType>,

  // Extended field types for properties
  extended: {
    'json': FIELD_TYPES.TEXTAREA,
    'array': FIELD_TYPES.CUSTOM,
    'object': FIELD_TYPES.CUSTOM,
    'email': FIELD_TYPES.TEXT,
    'url': FIELD_TYPES.TEXT,
  } as const satisfies Record<string, FieldType>,

  // Legacy field type mappings
  legacy: {
    'checkbox': FIELD_TYPES.BOOLEAN,
    'iteration-count': FIELD_TYPES.MAX_ITERATION,
    'person-select': FIELD_TYPES.PERSON_SELECT,
    'variable-textarea': FIELD_TYPES.VARIABLE_TEXTAREA,
  } as const satisfies Record<LegacyFieldType, FieldType>,
} as const;

/**
 * Normalizes any field type input to a UI FieldType
 * This is the single source of truth for field type conversion
 */
export function normalizeFieldType(fieldType: AnyFieldType): FieldType {
  // If it's already a UI field type, return as-is
  if (Object.values(FIELD_TYPES).includes(fieldType as FieldType)) {
    return fieldType as FieldType;
  }

  // Check domain types first (most common)
  if (fieldType in FIELD_TYPE_REGISTRY.domain) {
    return FIELD_TYPE_REGISTRY.domain[fieldType as DomainFieldType];
  }

  // Check extended types
  if (fieldType in FIELD_TYPE_REGISTRY.extended) {
    return FIELD_TYPE_REGISTRY.extended[fieldType as keyof typeof FIELD_TYPE_REGISTRY.extended];
  }

  // Check legacy types
  if (fieldType in FIELD_TYPE_REGISTRY.legacy) {
    return FIELD_TYPE_REGISTRY.legacy[fieldType as LegacyFieldType];
  }

  // Default fallback
  console.warn(`Unknown field type: ${fieldType}, defaulting to TEXT`);
  return FIELD_TYPES.TEXT;
}

/**
 * Type guard to check if a field type is a domain field type
 */
export function isDomainFieldType(fieldType: unknown): fieldType is DomainFieldType {
  return typeof fieldType === 'string' && fieldType in FIELD_TYPE_REGISTRY.domain;
}

/**
 * Type guard to check if a field type is a legacy field type
 */
export function isLegacyFieldType(fieldType: unknown): fieldType is LegacyFieldType {
  return typeof fieldType === 'string' && fieldType in FIELD_TYPE_REGISTRY.legacy;
}

/**
 * Get all field type mappings combined
 * Useful for components that need to handle all possible field types
 */
export function getAllFieldTypeMappings(): Record<string, FieldType> {
  return {
    ...FIELD_TYPE_REGISTRY.domain,
    ...FIELD_TYPE_REGISTRY.extended,
    ...FIELD_TYPE_REGISTRY.legacy,
  };
}

/**
 * Export convenience mappings for backward compatibility
 * These will be deprecated in future versions
 */
export const DOMAIN_TO_UI_FIELD_TYPE = FIELD_TYPE_REGISTRY.domain;
export const PROPERTY_TO_BASE_FIELD_TYPE = {
  ...FIELD_TYPE_REGISTRY.domain,
  ...FIELD_TYPE_REGISTRY.extended,
} as const;
export const LEGACY_TYPE_MAP = FIELD_TYPE_REGISTRY.legacy;