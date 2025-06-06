import type { NodeType } from '@/types';
import type { NodeConfigItem } from '../types';
import { startNodeConfig } from './start';
import { conditionNodeConfig } from './condition';
import { jobNodeConfig } from './job';
import { endpointNodeConfig } from './endpoint';
import { personJobNodeConfig } from './personJob';
import { personBatchJobNodeConfig } from './personBatchJob';
import { dbNodeConfig } from './db';
import { userResponseNodeConfig } from './userResponse';
import { notionNodeConfig } from './notion';

export const NODE_CONFIGS: Record<NodeType, NodeConfigItem> = {
  start: startNodeConfig,
  condition: conditionNodeConfig,
  job: jobNodeConfig,
  endpoint: endpointNodeConfig,
  person_job: personJobNodeConfig,
  person_batch_job: personBatchJobNodeConfig,
  db: dbNodeConfig,
  user_response: userResponseNodeConfig,
  notion: notionNodeConfig
} as const;

export * from './start';
export * from './condition';
export * from './job';
export * from './endpoint';
export * from './personJob';
export * from './personBatchJob';
export * from './db';
export * from './userResponse';
export * from './notion';