/**
 * Node specification registry
 * Central location for all node specifications
 */

import { NodeSpecification, NodeSpecificationRegistry } from './node-specification.js';

// Import all node specifications
import { startSpec } from './nodes/start.spec.js';
import { personJobSpec } from './nodes/person-job.spec.js';
import { conditionSpec } from './nodes/condition.spec.js';
import { codeJobSpec } from './nodes/code-job.spec.js';
import { apiJobSpec } from './nodes/api-job.spec.js';
import { endpointSpec } from './nodes/endpoint.spec.js';
import { dbSpec } from './nodes/db.spec.js';
import { diffPatchSpec } from './nodes/diff-patch.spec.js';
import { userResponseSpec } from './nodes/user-response.spec.js';
import { hookSpec } from './nodes/hook.spec.js';
import { templateJobSpec } from './nodes/template-job.spec.js';
import { jsonSchemaValidatorSpec } from './nodes/json-schema-validator.spec.js';
import { typescriptAstSpec } from './nodes/typescript-ast.spec.js';
import { subDiagramSpec } from './nodes/sub-diagram.spec.js';
import { integratedApiSpec } from './nodes/integrated-api.spec.js';
import { irBuilderSpec } from './nodes/ir-builder.spec.js';

// Build the registry
export const nodeSpecificationRegistry: NodeSpecificationRegistry = {
  start: startSpec,
  person_job: personJobSpec,
  condition: conditionSpec,
  code_job: codeJobSpec,
  api_job: apiJobSpec,
  endpoint: endpointSpec,
  db: dbSpec,
  diff_patch: diffPatchSpec,
  user_response: userResponseSpec,
  hook: hookSpec,
  template_job: templateJobSpec,
  json_schema_validator: jsonSchemaValidatorSpec,
  typescript_ast: typescriptAstSpec,
  sub_diagram: subDiagramSpec,
  integrated_api: integratedApiSpec,
  ir_builder: irBuilderSpec,
};

// Export convenience function to get a specification by node type
export function getNodeSpecification(nodeType: string): NodeSpecification | undefined {
  return nodeSpecificationRegistry[nodeType];
}
