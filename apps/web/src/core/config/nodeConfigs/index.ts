import type { NodeType } from '@dipeo/domain-models';
import type { UnifiedNodeConfig } from '../unifiedConfig';

// Import all unified configs
import { startConfig } from './start';
import { conditionConfig } from './condition';
import { jobConfig } from './job';
import { endpointConfig } from './endpoint';
import { personJobConfig } from './personJob';
import { personBatchJobConfig } from './personBatchJob';
import { dbConfig } from './db';
import { userResponseConfig } from './userResponse';
import { notionConfig } from './notion';

export const UNIFIED_NODE_CONFIGS: Record<NodeType, UnifiedNodeConfig<any>> = {
  start: startConfig,
  condition: conditionConfig,
  job: jobConfig,
  endpoint: endpointConfig,
  person_job: personJobConfig,
  person_batch_job: personBatchJobConfig,
  db: dbConfig,
  user_response: userResponseConfig,
  notion: notionConfig
};

// Export individual configs
export { startConfig } from './start';
export { conditionConfig } from './condition';
export { jobConfig } from './job';
export { endpointConfig } from './endpoint';
export { personJobConfig } from './personJob';
export { personBatchJobConfig } from './personBatchJob';
export { dbConfig } from './db';
export { userResponseConfig } from './userResponse';
export { notionConfig } from './notion';