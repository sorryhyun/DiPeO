/**
 * Enumerations for GraphQL query generation system
 */

/**
 * GraphQL operation types
 */
export enum QueryOperationType {
  QUERY = 'query',
  MUTATION = 'mutation',
  SUBSCRIPTION = 'subscription'
}

/**
 * CRUD operation types for standardized query generation
 */
export enum CrudOperation {
  GET = 'get',
  LIST = 'list',
  CREATE = 'create',
  UPDATE = 'update',
  DELETE = 'delete',
  SUBSCRIBE = 'subscribe'
}

/**
 * System entities that can be queried
 */
export enum QueryEntity {
  DIAGRAM = 'Diagram',
  PERSON = 'Person',
  EXECUTION = 'Execution',
  API_KEY = 'ApiKey',
  CONVERSATION = 'Conversation',
  FILE = 'File',
  NODE = 'Node',
  PROMPT_TEMPLATE = 'PromptTemplate',
  SYSTEM = 'System'
}

/**
 * Field selection presets for different levels of detail
 */
export enum FieldPreset {
  MINIMAL = 'minimal',    // Only essential fields (id, name/label)
  STANDARD = 'standard',  // Common fields for normal operations
  DETAILED = 'detailed',  // Additional fields for detailed views
  FULL = 'full'          // All available fields
}

/**
 * Common field groups that appear across multiple entities
 */
export enum FieldGroup {
  METADATA = 'metadata',
  TIMESTAMPS = 'timestamps',
  RELATIONSHIPS = 'relationships',
  CONFIGURATION = 'configuration'
}
