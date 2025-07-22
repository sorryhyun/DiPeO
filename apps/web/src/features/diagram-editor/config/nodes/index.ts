/**
 * Export all unified node configurations
 */
export { StartNodeConfig } from './start';
export { PersonJobNodeConfig } from './person-job';
export { ConditionNodeConfig } from './condition';
export { EndpointNodeConfig } from './endpoint';
export { JobNodeConfig } from './job';
export { CodeJobNodeConfig } from './code-job';
export { ApiJobNodeConfig } from './api-job';
export { DbNodeConfig } from './db';
export { PersonBatchJobNodeConfig } from './person-batch-job';
export { UserResponseNodeConfig } from './user-response';
export { NotionNodeConfig } from './notion';
export { HookNodeConfig } from './hook';
export { TemplateJobNodeConfig } from './template-job';
export { JsonSchemaValidatorNodeConfig } from './json-schema-validator';
export { TypescriptAstNodeConfig } from './generated/typescriptAstConfig';
export { SubDiagramNodeConfig } from './generated/subDiagramConfig';

// Import all configurations for the map
import { StartNodeConfig } from './start';
import { PersonJobNodeConfig } from './person-job';
import { ConditionNodeConfig } from './condition';
import { EndpointNodeConfig } from './endpoint';
import { CodeJobNodeConfig } from './code-job';
import { ApiJobNodeConfig } from './api-job';
import { DbNodeConfig } from './db';
import { JobNodeConfig } from './job';
import { PersonBatchJobNodeConfig } from './person-batch-job';
import { UserResponseNodeConfig } from './user-response';
import { NotionNodeConfig } from './notion';
import { HookNodeConfig } from './hook';
import { TemplateJobNodeConfig } from './template-job';
import { JsonSchemaValidatorNodeConfig } from './json-schema-validator';
import { TypescriptAstNodeConfig } from './generated/typescriptAstConfig';
import { SubDiagramNodeConfig } from './generated/subDiagramConfig';

import { NodeType } from '@dipeo/domain-models';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';

/**
 * Map of all node configurations indexed by NodeType
 * This replaces the distributed configuration system from core
 */
export const NODE_CONFIGS_MAP: Record<NodeType, UnifiedNodeConfig<any>> = {
  [NodeType.START]: StartNodeConfig,
  [NodeType.PERSON_JOB]: PersonJobNodeConfig,
  [NodeType.CONDITION]: ConditionNodeConfig,
  [NodeType.ENDPOINT]: EndpointNodeConfig,
  [NodeType.CODE_JOB]: CodeJobNodeConfig,
  [NodeType.API_JOB]: ApiJobNodeConfig,
  [NodeType.DB]: DbNodeConfig,
  [NodeType.JOB]: JobNodeConfig,
  [NodeType.PERSON_BATCH_JOB]: PersonBatchJobNodeConfig,
  [NodeType.USER_RESPONSE]: UserResponseNodeConfig,
  [NodeType.NOTION]: NotionNodeConfig,
  [NodeType.HOOK]: HookNodeConfig,
  [NodeType.TEMPLATE_JOB]: TemplateJobNodeConfig,
  [NodeType.JSON_SCHEMA_VALIDATOR]: JsonSchemaValidatorNodeConfig,
  [NodeType.TYPESCRIPT_AST]: TypescriptAstNodeConfig,
  [NodeType.SUB_DIAGRAM]: SubDiagramNodeConfig,
};

/**
 * Helper function to get node configuration by type
 */
export function getNodeConfig(nodeType: NodeType): UnifiedNodeConfig<any> | undefined {
  return NODE_CONFIGS_MAP[nodeType];
}

// Export helper utilities
export * from './helpers';
export * from './nodeMeta';