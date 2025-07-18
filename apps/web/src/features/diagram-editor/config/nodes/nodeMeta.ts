import { NodeType } from '@dipeo/domain-models';

// Import individual configs to avoid circular dependency
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

/**
 * Node visual metadata extracted from configurations
 */
export const NODE_ICONS: Record<NodeType, string> = {
  [NodeType.START]: StartNodeConfig.icon,
  [NodeType.PERSON_JOB]: PersonJobNodeConfig.icon,
  [NodeType.CONDITION]: ConditionNodeConfig.icon,
  [NodeType.ENDPOINT]: EndpointNodeConfig.icon,
  [NodeType.CODE_JOB]: CodeJobNodeConfig.icon,
  [NodeType.API_JOB]: ApiJobNodeConfig.icon,
  [NodeType.DB]: DbNodeConfig.icon,
  [NodeType.JOB]: JobNodeConfig.icon,
  [NodeType.PERSON_BATCH_JOB]: PersonBatchJobNodeConfig.icon,
  [NodeType.USER_RESPONSE]: UserResponseNodeConfig.icon,
  [NodeType.NOTION]: NotionNodeConfig.icon,
  [NodeType.HOOK]: HookNodeConfig.icon,
};

export const NODE_COLORS: Record<NodeType, string> = {
  [NodeType.START]: StartNodeConfig.color,
  [NodeType.PERSON_JOB]: PersonJobNodeConfig.color,
  [NodeType.CONDITION]: ConditionNodeConfig.color,
  [NodeType.ENDPOINT]: EndpointNodeConfig.color,
  [NodeType.CODE_JOB]: CodeJobNodeConfig.color,
  [NodeType.API_JOB]: ApiJobNodeConfig.color,
  [NodeType.DB]: DbNodeConfig.color,
  [NodeType.JOB]: JobNodeConfig.color,
  [NodeType.PERSON_BATCH_JOB]: PersonBatchJobNodeConfig.color,
  [NodeType.USER_RESPONSE]: UserResponseNodeConfig.color,
  [NodeType.NOTION]: NotionNodeConfig.color,
  [NodeType.HOOK]: HookNodeConfig.color,
};

export const NODE_LABELS: Record<NodeType, string> = {
  [NodeType.START]: StartNodeConfig.label,
  [NodeType.PERSON_JOB]: PersonJobNodeConfig.label,
  [NodeType.CONDITION]: ConditionNodeConfig.label,
  [NodeType.ENDPOINT]: EndpointNodeConfig.label,
  [NodeType.CODE_JOB]: CodeJobNodeConfig.label,
  [NodeType.API_JOB]: ApiJobNodeConfig.label,
  [NodeType.DB]: DbNodeConfig.label,
  [NodeType.JOB]: JobNodeConfig.label,
  [NodeType.PERSON_BATCH_JOB]: PersonBatchJobNodeConfig.label,
  [NodeType.USER_RESPONSE]: UserResponseNodeConfig.label,
  [NodeType.NOTION]: NotionNodeConfig.label,
  [NodeType.HOOK]: HookNodeConfig.label,
};

/**
 * Generate a default label for a node
 */
export function generateNodeLabel(type: NodeType, id: string): string {
  const label = NODE_LABELS[type] || 'Node';
  const suffix = id.slice(-4).toUpperCase();
  return `${label} ${suffix}`;
}