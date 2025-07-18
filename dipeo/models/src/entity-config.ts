/**
 * Entity definition configuration for code generation
 * This defines the structure for declaring entities that will be used to generate
 * GraphQL resolvers, React hooks, and other boilerplate code
 */

export interface EntityDefinition {
  /** Entity name (singular, PascalCase) */
  name: string;
  
  /** Plural form of the entity name */
  plural: string;
  
  /** Entity fields definition */
  fields: Record<string, FieldDefinition>;
  
  /** Relations to other entities */
  relations?: Record<string, RelationDefinition>;
  
  /** Operations available for this entity */
  operations: OperationsDefinition;
  
  /** Additional features for this entity */
  features?: FeaturesDefinition;
  
  /** Service configuration */
  service?: ServiceDefinition;
}

export interface FieldDefinition {
  /** Field type (primitive or branded type) */
  type: FieldType;
  
  /** Whether field is required */
  required?: boolean;
  
  /** Whether field is nullable */
  nullable?: boolean;
  
  /** Whether field is auto-generated (like ID, timestamps) */
  generated?: boolean;
  
  /** Default value for the field */
  default?: any;
  
  /** Validation rules */
  validation?: ValidationRules;
}

export type FieldType = 
  | 'string'
  | 'number'
  | 'boolean'
  | 'Date'
  | 'JSON'
  | BrandedType
  | `${string}[]`; // Array types

/** Branded types from the domain model */
export type BrandedType = 
  | 'NodeID'
  | 'DiagramID'
  | 'PersonID'
  | 'ExecutionID'
  | 'HandleID'
  | 'ArrowID'
  | 'ApiKeyID';

export interface RelationDefinition {
  /** Related entity type */
  type: string;
  
  /** Relation type */
  relation: 'one-to-one' | 'one-to-many' | 'many-to-many';
  
  /** Whether relation is required */
  required?: boolean;
  
  /** Inverse relation field name */
  inverse?: string;
}

export interface OperationsDefinition {
  /** Create operation configuration */
  create?: CreateOperationConfig | boolean;
  
  /** Update operation configuration */
  update?: UpdateOperationConfig | boolean;
  
  /** Delete operation configuration */
  delete?: DeleteOperationConfig | boolean;
  
  /** List operation configuration */
  list?: ListOperationConfig | boolean;
  
  /** Get single item operation configuration */
  get?: GetOperationConfig | boolean;
  
  /** Custom operations */
  custom?: Record<string, CustomOperationConfig>;
}

export interface CreateOperationConfig {
  /** Fields to include in create input */
  input: string[];
  
  /** Validation rules for input */
  validation?: Record<string, ValidationRules>;
  
  /** Custom logic to execute after creation */
  customLogic?: string;
  
  /** Whether to return the created entity */
  returnEntity?: boolean;
}

export interface UpdateOperationConfig {
  /** Fields to include in update input */
  input: string[];
  
  /** Whether all fields are optional (partial update) */
  partial?: boolean;
  
  /** Validation rules for input */
  validation?: Record<string, ValidationRules>;
  
  /** Custom logic to execute after update */
  customLogic?: string;
}

export interface DeleteOperationConfig {
  /** Whether to soft delete instead of hard delete */
  soft?: boolean;
  
  /** Custom logic to execute before deletion */
  customLogic?: string;
}

export interface ListOperationConfig {
  /** Fields available for filtering */
  filters?: string[];
  
  /** Fields available for sorting */
  sortable?: string[];
  
  /** Whether to enable pagination */
  pagination?: boolean;
  
  /** Default page size */
  defaultPageSize?: number;
  
  /** Maximum page size */
  maxPageSize?: number;
}

export interface GetOperationConfig {
  /** Additional fields to include */
  include?: string[];
  
  /** Whether to throw if not found */
  throwIfNotFound?: boolean;
}

export interface CustomOperationConfig {
  /** Operation name */
  name: string;
  
  /** Operation type */
  type: 'query' | 'mutation';
  
  /** Input fields */
  input?: string[];
  
  /** Return type */
  returns: string;
  
  /** Implementation */
  implementation: string;
}

export interface ValidationRules {
  /** Minimum length for strings */
  minLength?: number;
  
  /** Maximum length for strings */
  maxLength?: number;
  
  /** Pattern for string validation */
  pattern?: string;
  
  /** Minimum value for numbers */
  min?: number;
  
  /** Maximum value for numbers */
  max?: number;
  
  /** Custom validation function */
  custom?: string;
}

export interface FeaturesDefinition {
  /** Whether to add createdAt/updatedAt timestamps */
  timestamps?: boolean;
  
  /** Whether to enable soft delete */
  softDelete?: boolean;
  
  /** Whether to enable audit logging */
  audit?: boolean;
  
  /** Whether to enable versioning */
  versioning?: boolean;
  
  /** Whether to enable caching */
  cache?: boolean;
  
  /** Cache TTL in seconds */
  cacheTTL?: number;
}

export interface ServiceDefinition {
  /** Service name override */
  name?: string;
  
  /** Whether service is async */
  async?: boolean;
  
  /** Dependencies required by the service */
  dependencies?: string[];
}

/**
 * Helper function to define an entity with type checking
 */
export function defineEntity(config: EntityDefinition): EntityDefinition {
  return config;
}