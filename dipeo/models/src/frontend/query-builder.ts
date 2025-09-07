/**
 * Query builder utilities using TypeScript enums for type-safe query generation
 */

import { CrudOperation, QueryEntity, FieldPreset, QueryOperationType } from './query-enums';
import { QueryField, QuerySpecification, QueryVariable } from './query-specifications';

/**
 * Build a standardized query name from operation and entity
 */
export function buildQueryName(operation: CrudOperation, entity: QueryEntity): string {
  const entityName = entity.toString();

  switch (operation) {
    case CrudOperation.GET:
      return `Get${entityName}`;
    case CrudOperation.LIST:
      return `List${entityName}s`;
    case CrudOperation.CREATE:
      return `Create${entityName}`;
    case CrudOperation.UPDATE:
      return `Update${entityName}`;
    case CrudOperation.DELETE:
      return `Delete${entityName}`;
    case CrudOperation.SUBSCRIBE:
      return `Subscribe${entityName}`;
    default:
      throw new Error(`Unknown operation: ${operation}`);
  }
}

/**
 * Determine the GraphQL operation type for a CRUD operation
 */
export function getOperationType(crudOp: CrudOperation): QueryOperationType {
  switch (crudOp) {
    case CrudOperation.GET:
    case CrudOperation.LIST:
      return QueryOperationType.QUERY;
    case CrudOperation.CREATE:
    case CrudOperation.UPDATE:
    case CrudOperation.DELETE:
      return QueryOperationType.MUTATION;
    case CrudOperation.SUBSCRIBE:
      return QueryOperationType.SUBSCRIPTION;
    default:
      throw new Error(`Unknown CRUD operation: ${crudOp}`);
  }
}

/**
 * Get standard variables for a CRUD operation
 */
export function getStandardVariables(operation: CrudOperation, entity: QueryEntity): QueryVariable[] {
  const entityName = entity.toString();

  switch (operation) {
    case CrudOperation.GET:
      return [
        { name: 'id', type: 'ID', required: true }
      ];

    case CrudOperation.LIST:
      return [
        { name: 'offset', type: 'Int', required: false },
        { name: 'limit', type: 'Int', required: false },
        { name: 'filter', type: `${entityName}Filter`, required: false }
      ];

    case CrudOperation.CREATE:
      return [
        { name: 'input', type: `Create${entityName}Input`, required: true }
      ];

    case CrudOperation.UPDATE:
      return [
        { name: 'id', type: 'ID', required: true },
        { name: 'input', type: `Update${entityName}Input`, required: true }
      ];

    case CrudOperation.DELETE:
      return [
        { name: 'id', type: 'ID', required: true }
      ];

    case CrudOperation.SUBSCRIBE:
      return [
        { name: 'id', type: 'ID', required: false }
      ];

    default:
      return [];
  }
}

/**
 * Get return type for a CRUD operation
 */
export function getReturnType(operation: CrudOperation, entity: QueryEntity): string {
  const entityName = entity.toString();

  switch (operation) {
    case CrudOperation.GET:
    case CrudOperation.CREATE:
    case CrudOperation.UPDATE:
      return entityName;
    case CrudOperation.LIST:
      return `[${entityName}!]!`;
    case CrudOperation.DELETE:
      return 'Boolean!';
    case CrudOperation.SUBSCRIBE:
      return `${entityName}Event`;
    default:
      return entityName;
  }
}

/**
 * Build a complete query specification using enums
 */
export function buildQuerySpecification(
  operation: CrudOperation,
  entity: QueryEntity,
  fields: QueryField[],
  customVariables?: QueryVariable[]
): QuerySpecification {
  const entityName = entity.toString();

  return {
    name: buildQueryName(operation, entity),
    operation: getOperationType(operation),
    entityType: entityName,
    description: `${operation} operation for ${entityName}`,
    variables: customVariables || getStandardVariables(operation, entity),
    returnType: getReturnType(operation, entity),
    fields: fields
  };
}

/**
 * Get field preset for an entity
 */
export function getFieldPreset(entity: QueryEntity, preset: FieldPreset): QueryField[] {
  // This would be expanded with actual field definitions per entity and preset
  // For now, return a basic structure that can be customized per entity

  switch (preset) {
    case FieldPreset.MINIMAL:
      return [
        { name: 'id', required: true },
        { name: getMainLabelField(entity), required: true }
      ];

    case FieldPreset.STANDARD:
      return [
        { name: 'id', required: true },
        { name: getMainLabelField(entity), required: true },
        ...getStandardFields(entity)
      ];

    case FieldPreset.DETAILED:
    case FieldPreset.FULL:
      // These would include all fields for the entity
      return getAllFields(entity);

    default:
      return [];
  }
}

/**
 * Helper to get the main label field for an entity
 */
function getMainLabelField(entity: QueryEntity): string {
  switch (entity) {
    case QueryEntity.PERSON:
      return 'label';
    case QueryEntity.DIAGRAM:
    case QueryEntity.FILE:
    case QueryEntity.PROMPT_TEMPLATE:
      return 'name';
    case QueryEntity.EXECUTION:
    case QueryEntity.API_KEY:
      return 'id';
    case QueryEntity.CONVERSATION:
      return 'title';
    default:
      return 'name';
  }
}

/**
 * Get standard fields for an entity (placeholder - would be expanded)
 */
function getStandardFields(entity: QueryEntity): QueryField[] {
  // This would return entity-specific standard fields
  // For now, return common fields
  return [
    { name: 'created', required: false },
    { name: 'modified', required: false }
  ];
}

/**
 * Get all fields for an entity (placeholder - would be expanded)
 */
function getAllFields(entity: QueryEntity): QueryField[] {
  // This would return all available fields for the entity
  // Implementation would reference the actual field definitions
  return getStandardFields(entity);
}

/**
 * Type guard to check if a string is a valid CrudOperation
 */
export function isCrudOperation(value: string): value is CrudOperation {
  return Object.values(CrudOperation).includes(value as CrudOperation);
}

/**
 * Type guard to check if a string is a valid QueryEntity
 */
export function isQueryEntity(value: string): value is QueryEntity {
  return Object.values(QueryEntity).includes(value as QueryEntity);
}
