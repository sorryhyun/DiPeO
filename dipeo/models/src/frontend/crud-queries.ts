import { QuerySpecification } from './query-specifications';

export const createGetQuerySpec = (entity: string, fields: string[]): QuerySpecification => ({
  name: `get${entity}`,
  operation: 'query',
  entityType: entity,
  description: `Get a single ${entity} by ID`,
  variables: [
    {
      name: 'id',
      type: 'ID!',
      required: true
    }
  ],
  returnType: entity,
  fields: fields.map(f => ({ name: f, required: true }))
});

export const createListQuerySpec = (entity: string, fields: string[]): QuerySpecification => ({
  name: `list${entity}s`,
  operation: 'query',
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

export const createCreateMutationSpec = (entity: string, inputFields: string[]): QuerySpecification => ({
  name: `create${entity}`,
  operation: 'mutation',
  entityType: entity,
  description: `Create a new ${entity}`,
  variables: [
    {
      name: 'input',
      type: `Create${entity}Input!`,
      required: true
    }
  ],
  returnType: entity,
  fields: inputFields.map(f => ({ name: f, required: true }))
});

export const createUpdateMutationSpec = (entity: string, fields: string[]): QuerySpecification => ({
  name: `update${entity}`,
  operation: 'mutation',
  entityType: entity,
  description: `Update an existing ${entity}`,
  variables: [
    {
      name: 'id',
      type: 'ID!',
      required: true
    },
    {
      name: 'input',
      type: `Update${entity}Input!`,
      required: true
    }
  ],
  returnType: entity,
  fields: fields.map(f => ({ name: f, required: true }))
});

export const createDeleteMutationSpec = (entity: string): QuerySpecification => ({
  name: `delete${entity}`,
  operation: 'mutation',
  entityType: entity,
  description: `Delete a ${entity}`,
  variables: [
    {
      name: 'id',
      type: 'ID!',
      required: true
    }
  ],
  returnType: 'Boolean!',
  fields: []
});