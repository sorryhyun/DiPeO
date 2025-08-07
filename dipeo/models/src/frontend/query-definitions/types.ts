/**
 * Shared types for GraphQL query definitions
 */

import { QueryOperationType } from '../query-enums';

export interface FieldDefinition {
  name: string;
  fields?: FieldDefinition[];
}

export interface VariableDefinition {
  name: string;
  type: string;
  required?: boolean;
  defaultValue?: any;
}

export interface QueryDefinition {
  name: string;
  type: QueryOperationType;
  variables?: VariableDefinition[];
  fields: FieldDefinition[];
  description?: string;
}

export interface EntityQueryDefinitions {
  entity: string;
  queries: QueryDefinition[];
}