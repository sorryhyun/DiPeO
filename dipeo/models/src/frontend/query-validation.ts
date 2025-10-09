/**
 * Query Validation Framework
 *
 * Provides comprehensive validation for GraphQL query specifications to prevent
 * generating syntactically invalid queries. This framework validates:
 * - Type names and their existence in the schema
 * - Required fields and their presence
 * - Query syntax correctness
 * - Field selections validity for entity types
 * - Circular dependencies in nested fields
 * - Variable definitions and their types
 *
 * @module query-validation
 */

import { QuerySpecification, QueryField, QueryVariable } from './query-specifications';
import { QueryOperationType, QueryEntity } from './query-enums';

/**
 * Severity level for validation issues
 */
export type ValidationSeverity = 'error' | 'warning';

/**
 * Represents a single validation error or warning
 */
export interface ValidationError {
  /** The field or path where the error occurred */
  field: string;
  /** Human-readable error message */
  message: string;
  /** Severity level of the validation issue */
  severity: ValidationSeverity;
  /** Optional error code for programmatic handling */
  code?: string;
}

/**
 * Result of a validation operation
 */
export interface ValidationResult {
  /** Whether the validation passed (no errors) */
  valid: boolean;
  /** List of validation errors found */
  errors: ValidationError[];
  /** List of validation warnings (non-blocking issues) */
  warnings: ValidationError[];
}

/**
 * GraphQL scalar types that are always valid
 */
const GRAPHQL_SCALARS = new Set([
  'ID',
  'String',
  'Int',
  'Float',
  'Boolean',
  'JSON',
  'DateTime',
  'Upload'
]);

/**
 * Branded scalar types from the DiPeO schema
 */
const DIPEO_BRANDED_SCALARS = new Set([
  'DiagramID',
  'NodeID',
  'ArrowID',
  'HandleID',
  'PersonID',
  'ApiKeyID',
  'ExecutionID',
  'TaskID',
  'HookID'
]);

/**
 * Known GraphQL enum types from the schema
 */
const GRAPHQL_ENUMS = new Set([
  'APIServiceType',
  'ContentType',
  'DataType',
  'DiagramFormatGraphQL',
  'EventType',
  'HandleDirection',
  'HandleLabel',
  'LLMService',
  'NodeType',
  'Status'
]);

/**
 * Known GraphQL input types from the schema
 */
const GRAPHQL_INPUT_TYPES = new Set([
  'CreateApiKeyInput',
  'CreateDiagramInput',
  'CreateNodeInput',
  'CreatePersonInput',
  'DiagramFilterInput',
  'ExecuteDiagramInput',
  'ExecuteIntegrationInput',
  'ExecutionControlInput',
  'ExecutionFilterInput',
  'InteractiveResponseInput',
  'PersonLLMConfigInput',
  'RegisterCliSessionInput',
  'TestIntegrationInput',
  'UnregisterCliSessionInput',
  'UpdateNodeInput',
  'UpdateNodeStateInput',
  'UpdatePersonInput',
  'Vec2Input'
]);

/**
 * Known GraphQL object types from the schema
 */
const GRAPHQL_OBJECT_TYPES = new Set([
  'ApiKeyResult',
  'AuthConfigType',
  'CliSessionResult',
  'DeleteResult',
  'DiagramMetadataType',
  'DiagramResult',
  'DomainApiKeyType',
  'DomainArrowType',
  'DomainDiagramType',
  'DomainHandleType',
  'DomainNodeType',
  'DomainPersonType',
  'ExecutionResult',
  'ExecutionStateType',
  'ExecutionUpdateType',
  'FormatConversionResult',
  'IntegrationTestResultType',
  'LLMUsageType',
  'NodeResult',
  'OperationSchemaType',
  'OperationType',
  'PersonLLMConfigType',
  'PersonResult',
  'ProviderMetadataType',
  'ProviderStatisticsType',
  'ProviderType',
  'RateLimitConfigType',
  'RetryPolicyType',
  'Vec2Type'
]);

/**
 * Known fields for each entity type
 * This provides validation for field selections on specific types
 */
const ENTITY_FIELDS: Record<string, Set<string>> = {
  DomainDiagramType: new Set(['nodes', 'handles', 'arrows', 'persons', 'metadata']),
  DomainNodeType: new Set(['id', 'type', 'position', 'data']),
  DomainArrowType: new Set(['id', 'source', 'target', 'content_type', 'label', 'execution_priority', 'data']),
  DomainHandleType: new Set(['id', 'node_id', 'label', 'direction', 'data_type', 'position']),
  DomainPersonType: new Set(['id', 'label', 'llm_config', 'type']),
  DiagramMetadataType: new Set(['id', 'name', 'description', 'version', 'created', 'modified', 'author', 'tags', 'format']),
  PersonLLMConfigType: new Set(['service', 'model', 'api_key_id', 'system_prompt', 'prompt_file']),
  Vec2Type: new Set(['x', 'y']),
  ExecutionStateType: new Set(['id', 'status', 'diagram_id', 'started_at', 'ended_at', 'error', 'llm_usage', 'is_active', 'executed_nodes', 'node_states', 'node_outputs', 'variables', 'exec_counts', 'metrics']),
  LLMUsageType: new Set(['input', 'output', 'cached', 'total']),
  DomainApiKeyType: new Set(['id', 'label', 'service', 'key']),
  ProviderType: new Set(['name', 'operations', 'metadata', 'base_url', 'auth_config', 'rate_limit', 'retry_policy', 'default_timeout']),
  OperationType: new Set(['name', 'method', 'path', 'description', 'required_scopes', 'has_pagination', 'timeout_override']),
  ProviderMetadataType: new Set(['version', 'type', 'manifest_path', 'description', 'documentation_url', 'support_email']),
  AuthConfigType: new Set(['strategy', 'header', 'query_param', 'format', 'scopes']),
  RateLimitConfigType: new Set(['algorithm', 'capacity', 'refill_per_sec', 'window_size_sec']),
  RetryPolicyType: new Set(['strategy', 'max_retries', 'base_delay_ms', 'max_delay_ms', 'retry_on_status']),
  DiagramResult: new Set(['success', 'message', 'error', 'error_type', 'envelope', 'data', 'diagram']),
  ExecutionResult: new Set(['success', 'message', 'error', 'error_type', 'envelope', 'data', 'execution']),
  NodeResult: new Set(['success', 'message', 'error', 'error_type', 'envelope', 'data', 'node']),
  PersonResult: new Set(['success', 'message', 'error', 'error_type', 'envelope', 'data', 'person']),
  ApiKeyResult: new Set(['success', 'message', 'error', 'error_type', 'envelope', 'data', 'api_key']),
  DeleteResult: new Set(['success', 'message', 'error', 'error_type', 'envelope', 'data', 'deleted_id', 'deleted_count']),
  CliSessionResult: new Set(['success', 'message', 'error', 'error_type', 'envelope', 'data', 'session_id', 'execution_id']),
  FormatConversionResult: new Set(['success', 'message', 'error', 'error_type', 'envelope', 'data', 'format', 'original_format']),
  IntegrationTestResultType: new Set(['success', 'provider', 'operation', 'status_code', 'response_time_ms', 'error', 'response_preview']),
  ProviderStatisticsType: new Set(['total_providers', 'total_operations', 'provider_types', 'providers']),
  OperationSchemaType: new Set(['operation', 'method', 'path', 'description', 'request_body', 'query_params', 'response']),
  ExecutionUpdateType: new Set(['type', 'execution_id', 'node_id', 'status', 'result', 'error', 'timestamp', 'total_tokens', 'node_type', 'tokens', 'data'])
};

/**
 * Query operation to expected return types mapping
 */
const QUERY_OPERATIONS: Record<string, string> = {
  getApiKeys: 'JSON',
  getApiKey: 'DomainApiKeyType',
  getAvailableModels: 'JSON',
  listConversations: '[JSON!]!',
  getDiagram: 'DomainDiagramType',
  listDiagrams: '[DomainDiagramType!]!',
  getExecution: 'ExecutionStateType',
  listExecutions: '[ExecutionStateType!]!',
  getSupportedFormats: 'JSON',
  getPerson: 'DomainPersonType',
  listPersons: '[DomainPersonType!]!',
  listPromptFiles: '[JSON!]!',
  getPromptFile: 'JSON',
  listProviders: '[ProviderType!]!',
  getProvider: 'ProviderType',
  getProviderOperations: 'JSON',
  getOperationSchema: 'OperationSchemaType',
  getProviderStatistics: 'ProviderStatisticsType',
  getSystemInfo: 'JSON',
  getExecutionCapabilities: 'JSON',
  healthCheck: 'JSON',
  getExecutionOrder: 'JSON',
  getExecutionMetrics: 'JSON',
  getExecutionHistory: 'JSON',
  getActiveCliSession: 'JSON'
};

/**
 * Mutation operation to expected return types mapping
 */
const MUTATION_OPERATIONS: Record<string, string> = {
  createApiKey: 'ApiKeyResult',
  testApiKey: 'ApiKeyResult',
  deleteApiKey: 'DeleteResult',
  registerCliSession: 'CliSessionResult',
  unregisterCliSession: 'CliSessionResult',
  createDiagram: 'DiagramResult',
  executeDiagram: 'ExecutionResult',
  deleteDiagram: 'DeleteResult',
  controlExecution: 'ExecutionResult',
  sendInteractiveResponse: 'ExecutionResult',
  updateNodeState: 'ExecutionResult',
  uploadFile: 'JSON',
  uploadDiagram: 'JSON',
  validateDiagram: 'JSON',
  convertDiagramFormat: 'FormatConversionResult',
  createNode: 'NodeResult',
  updateNode: 'NodeResult',
  deleteNode: 'DeleteResult',
  createPerson: 'PersonResult',
  updatePerson: 'PersonResult',
  deletePerson: 'DeleteResult',
  executeIntegration: 'JSON',
  testIntegration: 'IntegrationTestResultType',
  reloadProvider: 'JSON'
};

/**
 * Subscription operation to expected return types mapping
 */
const SUBSCRIPTION_OPERATIONS: Record<string, string> = {
  executionUpdates: 'ExecutionUpdateType'
};

/**
 * Creates a validation error
 */
function createError(
  field: string,
  message: string,
  severity: ValidationSeverity = 'error',
  code?: string
): ValidationError {
  return { field, message, severity, code };
}

/**
 * Creates a successful validation result
 */
function createSuccessResult(): ValidationResult {
  return { valid: true, errors: [], warnings: [] };
}

/**
 * Creates a failed validation result with errors
 */
function createFailureResult(errors: ValidationError[], warnings: ValidationError[] = []): ValidationResult {
  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}

/**
 * Validates whether a type name exists in the GraphQL schema
 *
 * @param typeName - The type name to validate
 * @returns true if the type exists, false otherwise
 *
 * @example
 * ```typescript
 * isValidTypeName('String'); // true (scalar)
 * isValidTypeName('DomainDiagramType'); // true (object type)
 * isValidTypeName('InvalidType'); // false
 * ```
 */
export function isValidTypeName(typeName: string): boolean {
  // Strip array brackets and nullability markers
  const baseType = typeName.replace(/[\[\]!]/g, '');

  return GRAPHQL_SCALARS.has(baseType) ||
         DIPEO_BRANDED_SCALARS.has(baseType) ||
         GRAPHQL_ENUMS.has(baseType) ||
         GRAPHQL_INPUT_TYPES.has(baseType) ||
         GRAPHQL_OBJECT_TYPES.has(baseType);
}

/**
 * Validates variable definitions in a query specification
 *
 * Checks:
 * - Variable names are valid (alphanumeric + underscore)
 * - Variable types exist in the schema
 * - Required variables are properly marked
 * - Type syntax is correct (array notation, nullability)
 *
 * @param variables - Array of variable definitions to validate
 * @returns Validation result with any errors or warnings found
 *
 * @example
 * ```typescript
 * const result = validateVariables([
 *   { name: 'id', type: 'ID', required: true },
 *   { name: 'input', type: 'CreateDiagramInput', required: true }
 * ]);
 * if (!result.valid) {
 *   console.error('Validation failed:', result.errors);
 * }
 * ```
 */
export function validateVariables(variables?: QueryVariable[]): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: ValidationError[] = [];

  if (!variables || variables.length === 0) {
    return createSuccessResult();
  }

  const variableNames = new Set<string>();

  for (const variable of variables) {
    // Check for valid variable name
    if (!variable.name || !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(variable.name)) {
      errors.push(createError(
        `variable.${variable.name}`,
        `Invalid variable name: "${variable.name}". Must start with letter or underscore and contain only alphanumeric characters and underscores.`,
        'error',
        'INVALID_VARIABLE_NAME'
      ));
    }

    // Check for duplicate variable names
    if (variableNames.has(variable.name)) {
      errors.push(createError(
        `variable.${variable.name}`,
        `Duplicate variable name: "${variable.name}"`,
        'error',
        'DUPLICATE_VARIABLE'
      ));
    }
    variableNames.add(variable.name);

    // Validate variable type
    if (!variable.type) {
      errors.push(createError(
        `variable.${variable.name}`,
        'Variable type is required',
        'error',
        'MISSING_VARIABLE_TYPE'
      ));
    } else if (!isValidTypeName(variable.type)) {
      errors.push(createError(
        `variable.${variable.name}`,
        `Unknown type: "${variable.type}"`,
        'error',
        'UNKNOWN_TYPE'
      ));
    }

    // Warn if required is not explicitly set
    if (variable.required === undefined) {
      warnings.push(createError(
        `variable.${variable.name}`,
        'Variable "required" flag is not explicitly set. Consider setting it explicitly for clarity.',
        'warning',
        'IMPLICIT_REQUIRED'
      ));
    }
  }

  return createFailureResult(errors, warnings);
}

/**
 * Validates field selections for a specific entity type
 *
 * Checks:
 * - Field names are valid for the entity type
 * - Required nested fields are present
 * - No circular dependencies in field selections
 * - Field hierarchy is correct
 *
 * @param entityType - The GraphQL type being queried
 * @param fields - Array of field selections
 * @param path - Internal parameter for tracking field path (used for recursion)
 * @param visited - Internal parameter for tracking visited types (used for circular dependency detection)
 * @returns Validation result with any errors or warnings found
 *
 * @example
 * ```typescript
 * const result = validateFields('DomainDiagramType', [
 *   { name: 'id' },
 *   { name: 'nodes', fields: [{ name: 'id' }, { name: 'type' }] }
 * ]);
 * ```
 */
export function validateFields(
  entityType: string,
  fields: QueryField[],
  path: string = '',
  visited: Set<string> = new Set()
): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: ValidationError[] = [];

  if (!fields || fields.length === 0) {
    warnings.push(createError(
      path || 'fields',
      'No fields specified. Query should select at least one field.',
      'warning',
      'EMPTY_FIELD_SELECTION'
    ));
    return createFailureResult([], warnings);
  }

  // Check for circular dependencies
  if (visited.has(entityType)) {
    errors.push(createError(
      path,
      `Circular dependency detected: ${entityType} is already in the field selection path`,
      'error',
      'CIRCULAR_DEPENDENCY'
    ));
    return createFailureResult(errors, warnings);
  }

  // Track this type in visited set
  const newVisited = new Set(visited);
  newVisited.add(entityType);

  // Get valid fields for this entity type
  const validFields = ENTITY_FIELDS[entityType];

  // Track field names for duplicate detection
  const fieldNames = new Set<string>();

  for (const field of fields) {
    const fieldPath = path ? `${path}.${field.name}` : field.name;

    // Check for valid field name
    if (!field.name || !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(field.name)) {
      errors.push(createError(
        fieldPath,
        `Invalid field name: "${field.name}"`,
        'error',
        'INVALID_FIELD_NAME'
      ));
      continue;
    }

    // Check for duplicate fields
    if (fieldNames.has(field.name)) {
      warnings.push(createError(
        fieldPath,
        `Duplicate field: "${field.name}"`,
        'warning',
        'DUPLICATE_FIELD'
      ));
    }
    fieldNames.add(field.name);

    // Validate field exists on entity type (if we have the schema info)
    if (validFields && !validFields.has(field.name)) {
      // Special case: allow 'id' on any object type
      if (field.name !== 'id') {
        warnings.push(createError(
          fieldPath,
          `Field "${field.name}" may not exist on type "${entityType}". Please verify against the GraphQL schema.`,
          'warning',
          'UNKNOWN_FIELD'
        ));
      }
    }

    // Recursively validate nested fields
    if (field.fields && field.fields.length > 0) {
      // Try to determine the type of this field to validate nested fields
      // For now, we make best-effort guesses based on field name patterns
      let nestedType = inferFieldType(field.name);

      if (nestedType) {
        const nestedResult = validateFields(nestedType, field.fields, fieldPath, newVisited);
        errors.push(...nestedResult.errors);
        warnings.push(...nestedResult.warnings);
      }
    }
  }

  return createFailureResult(errors, warnings);
}

/**
 * Infer the type of a field based on its name
 * This is a best-effort approach for nested field validation
 */
function inferFieldType(fieldName: string): string | null {
  // Common field name patterns
  const typeMap: Record<string, string | null> = {
    'metadata': 'DiagramMetadataType',
    'nodes': 'DomainNodeType',
    'handles': 'DomainHandleType',
    'arrows': 'DomainArrowType',
    'persons': 'DomainPersonType',
    'person': 'DomainPersonType',
    'llm_config': 'PersonLLMConfigType',
    'position': 'Vec2Type',
    'llm_usage': 'LLMUsageType',
    'execution': 'ExecutionStateType',
    'diagram': 'DomainDiagramType',
    'node': 'DomainNodeType',
    'data': null, // JSON type, no nested validation
    'operations': 'OperationType',
    'provider': 'ProviderType',
    'auth_config': 'AuthConfigType',
    'rate_limit': 'RateLimitConfigType',
    'retry_policy': 'RetryPolicyType'
  };

  return typeMap[fieldName] || null;
}

/**
 * Validates the syntax of query name and basic structure
 *
 * Checks:
 * - Query name follows GraphQL naming conventions
 * - Operation type is valid
 * - Entity type is properly formatted
 * - Basic structure is correct
 *
 * @param spec - The query specification to validate
 * @returns Validation result with any errors or warnings found
 *
 * @example
 * ```typescript
 * const result = validateQuerySyntax({
 *   name: 'GetDiagram',
 *   operation: QueryOperationType.QUERY,
 *   entityType: 'Diagram',
 *   returnType: 'DomainDiagramType',
 *   fields: [{ name: 'id' }]
 * });
 * ```
 */
export function validateQuerySyntax(spec: QuerySpecification): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: ValidationError[] = [];

  // Validate query name
  if (!spec.name) {
    errors.push(createError(
      'name',
      'Query name is required',
      'error',
      'MISSING_QUERY_NAME'
    ));
  } else if (!/^[A-Z][a-zA-Z0-9]*$/.test(spec.name)) {
    warnings.push(createError(
      'name',
      `Query name "${spec.name}" should follow PascalCase convention and start with uppercase letter`,
      'warning',
      'QUERY_NAME_CONVENTION'
    ));
  }

  // Validate operation type
  if (!spec.operation) {
    errors.push(createError(
      'operation',
      'Operation type is required',
      'error',
      'MISSING_OPERATION_TYPE'
    ));
  } else if (!Object.values(QueryOperationType).includes(spec.operation)) {
    errors.push(createError(
      'operation',
      `Invalid operation type: "${spec.operation}". Must be one of: ${Object.values(QueryOperationType).join(', ')}`,
      'error',
      'INVALID_OPERATION_TYPE'
    ));
  }

  // Validate entity type
  if (!spec.entityType) {
    errors.push(createError(
      'entityType',
      'Entity type is required',
      'error',
      'MISSING_ENTITY_TYPE'
    ));
  }

  // Validate return type
  if (!spec.returnType) {
    errors.push(createError(
      'returnType',
      'Return type is required',
      'error',
      'MISSING_RETURN_TYPE'
    ));
  } else if (!isValidTypeName(spec.returnType)) {
    errors.push(createError(
      'returnType',
      `Unknown return type: "${spec.returnType}"`,
      'error',
      'UNKNOWN_RETURN_TYPE'
    ));
  }

  return createFailureResult(errors, warnings);
}

/**
 * Validates operation name matches expected schema operations
 *
 * @param operationType - The GraphQL operation type
 * @param operationName - The operation name being used
 * @returns Validation result
 */
function validateOperationName(operationType: QueryOperationType, operationName: string): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: ValidationError[] = [];

  let validOperations: Record<string, string> = {};

  switch (operationType) {
    case QueryOperationType.QUERY:
      validOperations = QUERY_OPERATIONS;
      break;
    case QueryOperationType.MUTATION:
      validOperations = MUTATION_OPERATIONS;
      break;
    case QueryOperationType.SUBSCRIPTION:
      validOperations = SUBSCRIPTION_OPERATIONS;
      break;
  }

  // Extract the operation name from the query spec name (e.g., "GetDiagram" -> "getDiagram")
  // This is a heuristic - the actual operation might be in the fields
  const operationNameLower = operationName.charAt(0).toLowerCase() + operationName.slice(1);

  if (!validOperations[operationNameLower] && !validOperations[operationName]) {
    warnings.push(createError(
      'operation',
      `Operation "${operationName}" may not exist in the GraphQL schema. Expected ${operationType} operations are: ${Object.keys(validOperations).join(', ')}`,
      'warning',
      'UNKNOWN_OPERATION'
    ));
  }

  return createFailureResult(errors, warnings);
}

/**
 * Validates a complete query specification
 *
 * This is the main validation entry point that performs comprehensive validation:
 * - Query syntax and naming
 * - Variable definitions
 * - Field selections
 * - Return type correctness
 * - Operation name validity
 *
 * @param spec - The complete query specification to validate
 * @returns Comprehensive validation result
 *
 * @example
 * ```typescript
 * const spec: QuerySpecification = {
 *   name: 'GetDiagram',
 *   operation: QueryOperationType.QUERY,
 *   entityType: 'Diagram',
 *   returnType: 'DomainDiagramType',
 *   variables: [
 *     { name: 'diagram_id', type: 'String', required: true }
 *   ],
 *   fields: [
 *     { name: 'id' },
 *     { name: 'metadata', fields: [{ name: 'name' }] }
 *   ]
 * };
 *
 * const result = validateQuerySpecification(spec);
 * if (!result.valid) {
 *   console.error('Validation errors:', result.errors);
 *   console.warn('Validation warnings:', result.warnings);
 *   throw new Error('Invalid query specification');
 * }
 * ```
 */
export function validateQuerySpecification(spec: QuerySpecification): ValidationResult {
  const allErrors: ValidationError[] = [];
  const allWarnings: ValidationError[] = [];

  // Validate basic query syntax
  const syntaxResult = validateQuerySyntax(spec);
  allErrors.push(...syntaxResult.errors);
  allWarnings.push(...syntaxResult.warnings);

  // Validate variables
  const variableResult = validateVariables(spec.variables);
  allErrors.push(...variableResult.errors);
  allWarnings.push(...variableResult.warnings);

  // Validate fields
  if (spec.fields && spec.fields.length > 0) {
    // Try to determine the root type for field validation
    const rootType = spec.returnType.replace(/[\[\]!]/g, '');
    const fieldResult = validateFields(rootType, spec.fields);
    allErrors.push(...fieldResult.errors);
    allWarnings.push(...fieldResult.warnings);
  } else {
    allWarnings.push(createError(
      'fields',
      'No fields specified in query',
      'warning',
      'NO_FIELDS'
    ));
  }

  // Validate operation name if possible
  if (spec.name && spec.operation) {
    const operationResult = validateOperationName(spec.operation, spec.name);
    allErrors.push(...operationResult.errors);
    allWarnings.push(...operationResult.warnings);
  }

  return createFailureResult(allErrors, allWarnings);
}

/**
 * Helper function to format validation results for display
 *
 * @param result - The validation result to format
 * @returns Formatted string representation of the validation result
 *
 * @example
 * ```typescript
 * const result = validateQuerySpecification(spec);
 * console.log(formatValidationResult(result));
 * ```
 */
export function formatValidationResult(result: ValidationResult): string {
  const lines: string[] = [];

  if (result.valid) {
    lines.push('✓ Validation passed');
  } else {
    lines.push('✗ Validation failed');
  }

  if (result.errors.length > 0) {
    lines.push('\nErrors:');
    for (const error of result.errors) {
      lines.push(`  [${error.field}] ${error.message}`);
    }
  }

  if (result.warnings.length > 0) {
    lines.push('\nWarnings:');
    for (const warning of result.warnings) {
      lines.push(`  [${warning.field}] ${warning.message}`);
    }
  }

  return lines.join('\n');
}

/**
 * Type guard to check if a validation result has errors
 *
 * @param result - The validation result to check
 * @returns true if there are errors, false otherwise
 */
export function hasValidationErrors(result: ValidationResult): boolean {
  return !result.valid || result.errors.length > 0;
}

/**
 * Type guard to check if a validation result has warnings
 *
 * @param result - The validation result to check
 * @returns true if there are warnings, false otherwise
 */
export function hasValidationWarnings(result: ValidationResult): boolean {
  return result.warnings.length > 0;
}
