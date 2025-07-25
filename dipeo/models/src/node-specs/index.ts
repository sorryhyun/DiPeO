/**
 * Node specifications registry
 * Export all node specifications from this central location
 */

import { NodeSpecificationRegistry } from '../node-specifications.js';
import { personJobSpec } from './person-job.spec.js';
import { apiJobSpec } from './api-job.spec.js';
import { codeJobSpec } from './code-job.spec.js';
import { conditionSpec } from './condition.spec.js';
import { startSpec } from './start.spec.js';
import { dbSpec } from './db.spec.js';
import { endpointSpec } from './endpoint.spec.js';
import { userResponseSpec } from './user-response.spec.js';
import { subDiagramSpec } from './sub-diagram.spec.js';
import { templateJobSpec } from './template-job.spec.js';
import { jsonSchemaValidatorSpec } from './json-schema-validator.spec.js';
import { typescriptAstSpec } from './typescript-ast.spec.js';
import { notionSpec } from './notion.spec.js';
import { personBatchJobSpec } from './person-batch-job.spec.js';
import { hookSpec } from './hook.spec.js';

// Export individual specifications
export { 
  personJobSpec,
  apiJobSpec,
  codeJobSpec,
  conditionSpec,
  startSpec,
  dbSpec,
  endpointSpec,
  userResponseSpec,
  subDiagramSpec,
  templateJobSpec,
  jsonSchemaValidatorSpec,
  typescriptAstSpec,
  notionSpec,
  personBatchJobSpec,
  hookSpec
};

// Export complete registry
export const nodeSpecificationRegistry: NodeSpecificationRegistry = {
  person_job: personJobSpec,
  api_job: apiJobSpec,
  code_job: codeJobSpec,
  condition: conditionSpec,
  start: startSpec,
  db: dbSpec,
  endpoint: endpointSpec,
  user_response: userResponseSpec,
  sub_diagram: subDiagramSpec,
  template_job: templateJobSpec,
  json_schema_validator: jsonSchemaValidatorSpec,
  typescript_ast: typescriptAstSpec,
  notion: notionSpec,
  person_batch_job: personBatchJobSpec,
  hook: hookSpec
};