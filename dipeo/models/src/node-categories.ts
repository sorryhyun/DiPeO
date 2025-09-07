/**
 * UI and specification-related type definitions
 */

// Node categories for UI organization
export type NodeCategory = 'control' | 'ai' | 'compute' | 'data' | 'integration' | 'interaction' | 'codegen' | 'validation' | 'utility';

// Field types that can be used in node specifications
export type FieldType = 'string' | 'number' | 'boolean' | 'array' | 'object' | 'enum' | 'any';

// UI input types for field rendering
export type UIInputType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'checkbox'
  | 'select'
  | 'code'
  | 'group'
  | 'json'
  | 'personSelect'  // Special person selector
  | 'nodeSelect';   // Node reference selector
