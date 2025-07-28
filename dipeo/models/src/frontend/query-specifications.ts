export interface QueryField {
  name: string;
  required?: boolean;
  fields?: QueryField[];
}

export interface QueryVariable {
  name: string;
  type: string;
  required: boolean;
}

export interface QuerySpecification {
  name: string;
  operation: 'query' | 'mutation' | 'subscription';
  entityType: string;
  description?: string;
  variables?: QueryVariable[];
  returnType: string;
  fields: QueryField[];
  template?: string;
}

export interface EntityQueryConfig {
  entity: string;
  operations: ('get' | 'list' | 'create' | 'update' | 'delete' | 'subscribe')[];
  defaultFields: QueryField[];
  relationships?: {
    name: string;
    type: string;
    fields: QueryField[];
  }[];
}

export interface QueryManifest {
  version: string;
  entities: EntityQueryConfig[];
}