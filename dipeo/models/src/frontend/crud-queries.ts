import { QuerySpecification, QueryField } from './query-specifications';
import { QueryOperationType, CrudOperation, QueryEntity } from './query-enums';
import { buildQueryName, getOperationType, getStandardVariables, getReturnType } from './query-builder';

/**
 * Create a GET query specification
 * @deprecated Use buildQuerySpecification from query-builder instead
 */
export const createGetQuerySpec = (entity: string, fields: string[]): QuerySpecification => ({
  name: `Get${entity}`,
  operation: QueryOperationType.QUERY,
  entityType: entity,
  description: `Get a single ${entity} by ID`,
  variables: [
    {
      name: 'id',
      type: 'ID',
      required: true
    }
  ],
  returnType: entity,
  fields: fields.map(f => ({ name: f, required: true }))
});

/**
 * Create a LIST query specification
 * @deprecated Use buildQuerySpecification from query-builder instead
 */
export const createListQuerySpec = (entity: string, fields: string[]): QuerySpecification => ({
  name: `List${entity}s`,
  operation: QueryOperationType.QUERY,
  entityType: entity,
  description: `List all ${entity}s with optional filtering`,
  variables: [
    {
      name: 'offset',
      type: 'Int',
      required: false
    },
    {
      name: 'limit',
      type: 'Int',
      required: false
    },
    {
      name: 'filter',
      type: `${entity}Filter`,
      required: false
    }
  ],
  returnType: `[${entity}!]!`,
  fields: fields.map(f => ({ name: f, required: true }))
});

/**
 * Create a CREATE mutation specification
 * @deprecated Use buildQuerySpecification from query-builder instead
 */
export const createCreateMutationSpec = (entity: string, inputFields: string[]): QuerySpecification => ({
  name: `Create${entity}`,
  operation: QueryOperationType.MUTATION,
  entityType: entity,
  description: `Create a new ${entity}`,
  variables: [
    {
      name: 'input',
      type: `Create${entity}Input`,
      required: true
    }
  ],
  returnType: entity,
  fields: inputFields.map(f => ({ name: f, required: true }))
});

/**
 * Create an UPDATE mutation specification
 * @deprecated Use buildQuerySpecification from query-builder instead
 */
export const createUpdateMutationSpec = (entity: string, fields: string[]): QuerySpecification => ({
  name: `Update${entity}`,
  operation: QueryOperationType.MUTATION,
  entityType: entity,
  description: `Update an existing ${entity}`,
  variables: [
    {
      name: 'id',
      type: 'ID',
      required: true
    },
    {
      name: 'input',
      type: `Update${entity}Input`,
      required: true
    }
  ],
  returnType: entity,
  fields: fields.map(f => ({ name: f, required: true }))
});

/**
 * Create a DELETE mutation specification
 * @deprecated Use buildQuerySpecification from query-builder instead
 */
export const createDeleteMutationSpec = (entity: string): QuerySpecification => ({
  name: `Delete${entity}`,
  operation: QueryOperationType.MUTATION,
  entityType: entity,
  description: `Delete a ${entity}`,
  variables: [
    {
      name: 'id',
      type: 'ID',
      required: true
    }
  ],
  returnType: 'Boolean!',
  fields: []
});