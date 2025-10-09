/**
 * UI and specification-related type definitions
 */

// Node categories for UI organization
export type NodeCategory = 'control' | 'ai' | 'compute' | 'data' | 'integration' | 'interaction' | 'codegen' | 'validation' | 'utility';

// Branded ID types (compile-time type safety for IDs)
export type BrandedIDType =
  | 'PersonID'
  | 'NodeID'
  | 'HandleID'
  | 'ArrowID'
  | 'ApiKeyID'
  | 'DiagramID'
  | 'ExecutionID'
  | 'FileID';

// Field types that can be used in node specifications
export type FieldType =
  | 'string'
  | 'number'
  | 'boolean'
  | 'array'
  | 'object'
  | 'enum'
  | 'any'
  | BrandedIDType;

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
  | 'personSelect'    // Special person selector (for PersonID)
  | 'nodeSelect'      // Node reference selector (for NodeID)
  | 'apiKeySelect'    // API key selector (for ApiKeyID)
  | 'diagramSelect'   // Diagram selector (for DiagramID)
  | 'fileSelect';     // File selector (for FileID)
